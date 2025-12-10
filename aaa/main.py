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
    print(f"{datetime.datetime.now()}: 文字起こしをします。")
    transcription = record_and_transcribe(stream)
    
    
    if transcription:
        print("\n---最終的な文字起こし結果---")
        print(transcription)
        print("--------------------------\n")

        result = detect_fraud(transcription, mode)

       result = detect_fraud(transcription, mode)
    print(f"LLM生ログ: {result}") # デバッグ用に表示

    # --- ここから修正部分 ---
    
    # 1. 詐欺確率の抽出 (fraud_probability:数字)
    # \s* はスペースがあってもOKという意味です
    match_prob = re.search(r"fraud_probability\s*[::]\s*(\d+)", result)
    
    # 2. 判定理由の抽出 (reason:文字, または改行まで)
    # (?=,|$|alert_level) は「カンマ」か「文末」か「alert_level」の手前まで取るという意味
    match_reason = re.search(r"reason\s*[::]\s*(.+?)(?=\s*,\s*alert_level|\s*$)", result)
    
    # 3. 危険度の抽出 (alert_level:safe/warning/danger)
    match_alert = re.search(r"alert_level\s*[::]\s*[\"']?(safe|warning|danger)[\"']?", result)

    # --- データの取得と処理 ---
    
    # 確率 (取れなかったら0にする)
    probability = int(match_prob.group(1)) if match_prob else 0
    
    # 理由 (取れなかったら"不明"にする)
    reason_text = match_reason.group(1).strip() if match_reason else "解析不能"
    
    # 危険度 (取れなかったら"unknown"にする)
    alert_lvl = match_alert.group(1) if match_alert else "unknown"

    print(f"解析結果 -> 確率:{probability}%, 危険度:{alert_lvl}, 理由:{reason_text}")

    # --- 判定ロジック ---
    # 確率70%以上、または alert_level が danger の場合に警告
    if probability >= 70 or alert_lvl == "danger":
        print("【警告】: 詐欺の可能性が非常に高いです")
        send_alert_email()
        
    elif alert_lvl == "warning":
        print("【注意】: 少し怪しい会話が含まれています")
        
    else:
        print("詐欺の可能性は低いです")

if __name__ == "__main__":
    main()
    