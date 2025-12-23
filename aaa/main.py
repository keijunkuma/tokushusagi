import sys
import os
import re
import smtplib
from email.mime.text import MIMEText
import ssl
import datetime
import pyaudio
from scipy.io.wavfile import read
from scipy.signal import spectrogram
import numpy as np
# --- 自作モジュール（ファイル）のインポート ---
from audio import record_and_transcribe 
from test import detect_fraud, load_local_model
from zeroitihantei import zeroiti, interval
from phonenumber import number_display, print_bytes, decode_fsk, decode_bytes
from bbb import itinokazu,countiti
from gemini import tokutei
from mail import send_alert_email
from audio import record_chunk
# --- 環境変数の読み込み ---
# --- ここまで ---

FORMAT = pyaudio.paInt16 #2の補数として16bitで表現　
CHANNELS = 1
RATE = 48000  # サンプリングレート (Hz)1秒間に48000回電圧の変化を確認しにいっている
RECORD_SECONDS = 2 # 録音時間 (秒)
INTERVAL_SECONDS = 0.01  # 分析間隔 (秒)
CHUNK = 1024
# 閾値設定
THRESHOLD = 0.1 # 音量の最大値の閾値
denwabangou = None  # ← まず初期値を設定する

def get_audio(stream,record_seconds):
    # 1秒間に含まれるデータ数
    total_frames = int(RATE * record_seconds)
    data = stream.read(total_frames, exception_on_overflow=False) #16bit(2byte)*total_frames
    return data

def main():
    mode = sys.argv[1]
    print(f"'{mode}'モードで詐欺検知システムを起動します。")
    audio = pyaudio.PyAudio()
    for i in range(audio.get_device_count()):
        print( audio.get_device_info_by_index(i))
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=4, frames_per_buffer=48000*300) #48000hzごとにformatで録音

    while True :
        data = get_audio(stream, 0.2)
        #この0.5秒でとる予定の物は捨てる最初のいらない音を捨てる
        result_list = zeroiti(data, RATE, INTERVAL_SECONDS, 0.2)
        print("aaa")
        #リストの中に1があるかどうか
        if 1 in result_list:
            print("初期微動計測")
            break
        else:
            print("bbb")


     
    # 音声データを読み込む
    data = get_audio(stream, 2)
    result_list = zeroiti(data, RATE, 0.1, THRESHOLD)
    if 10 <= countiti(result_list) <=12:
        data = get_audio(stream, 1)
        #ナンバーディスプレイの信号があるかどうか判定
        result_list = zeroiti(data, RATE, INTERVAL_SECONDS, 0.03)
        index1,index2 = itinokazu(result_list)
        start_byte_index = (index1 + 1)  * 2 * INTERVAL_SECONDS * RATE 
        end_byte_index = index2 * 2 * INTERVAL_SECONDS * RATE
        data = data[int(start_byte_index ):int(end_byte_index)]
        print("ccc")
        
        if  index1 != -1:
            # バイナリデータをnp.int16の配列に変換し、正規化
            signal = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            print(f"{datetime.datetime.now()}: ナンバーディスプレイのパターンを検知しました。電話番号の検知と文字起こしを開始します。")
            # デコード処理を実行
            decoded_data = decode_fsk(signal, 1200, 2100, 1300, 48000)
            print(decoded_data)
            decoded_bytes = decode_bytes(decoded_data)
            print_bytes(decoded_bytes)
            denwabangou1 = number_display(decoded_bytes)
            print("ddd")
            # デコード処理を実行
            decoded_data = decode_fsk(signal[20:], 1200, 2100, 1300, 48000)
            print(decoded_data)
            decoded_bytes = decode_bytes(decoded_data)
            print_bytes(decoded_bytes)
            #denwabangou2 = number_display(decoded_bytes)
            # 最後にまとめて、どちらかの番号が条件に合うかチェックします
            # まず denwabangou1 をチェック
            #if denwabangou1 and denwabangou1.isdigit() and len(denwabangou1) >= 10:
                #denwabangou = denwabangou1
            # denwabangou1 が条件に合わなければ、次に denwabangou2 をチェック
            #elif denwabangou2 and denwabangou2.isdigit() and len(denwabangou2) >= 10:
                #denwabangou = denwabangou2
            # 値が代入されているかチェックしてから関数を呼ぶ
            #if denwabangou is not None:
                #ayasii = tokutei(denwabangou)
            #else:
                #print("エラー: 電話番号が取得できませんでした。")
            #print("ddd")
    
    #whisper処理  
    full_history = ""  # 会話の履歴を保存する変数
    
    while True:
        # 1. 20秒間録音して文字にする
        # audio.pyの record_chunk は (テキスト, 終了フラグ) を返します
        text_chunk, is_finished = record_chunk(stream, duration=20)
        
        # 2. テキストがあれば履歴に追加して判定
        if text_chunk:
            full_history += text_chunk + " "
            print(f"\n--- 現在の会話ログ ---\n{full_history}\n----------------------")

            # 3. LLMで詐欺判定
            result = detect_fraud(full_history, mode)
            print(f"LLM判定結果: {result}")

            # --- 結果の解析 (正規表現) ---
            match_prob = re.search(r"fraud_probability\s*[::]\s*(\d+)", result)
            match_reason = re.search(r"reason\s*[::]\s*(.+?)(?=\s*,\s*alert_level|\s*$)", result)
            match_alert = re.search(r"alert_level\s*[::]\s*[\"']?(safe|warning|danger)[\"']?", result)

            probability = int(match_prob.group(1)) if match_prob else 0
            alert_lvl = match_alert.group(1) if match_alert else "unknown"
            reason_text = match_reason.group(1).strip() if match_reason else "解析不能"

            print(f"解析ステータス -> 危険度:{alert_lvl} (確率:{probability}%)")

            # 4. 危険なら即警告して終了（または継続して警告）
            if probability >= 80 or alert_lvl == "danger":
                print("\n【緊急警告】詐欺の可能性が極めて高いです！警告メールを送信します！")
                send_alert_email()
                # ここで break すれば警告してシステム終了。
                # break せずに continue すれば、監視を続けて何度も警告を送る。
                # 今回は誤検知も考慮して、とりあえずループは抜けないでおきます。
                
            elif alert_lvl == "warning":
                print("【注意】怪しい会話の可能性があります。")

        # 5. 通話終了（無音）ならループを抜ける
        if is_finished:
            print("通話が終了したため、監視を停止します。")
            break

    # 最終確認
    print("システム終了")

if __name__ == "__main__":
    main()
    