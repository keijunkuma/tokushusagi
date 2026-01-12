import sys
import os
import re
import smtplib
from email.mime.text import MIMEText
import ssl
import datetime
import pyaudio
import subprocess 
import time       
from scipy.io.wavfile import read
from scipy.signal import spectrogram
import numpy as np
import json 

# --- 自作モジュール（ファイル）のインポート ---
from test import detect_fraud, load_local_model
from zeroitihantei import zeroiti, interval
from phonenumber import number_display, print_bytes, decode_fsk, decode_bytes
from bbb import itinokazu, countiti
from gemini import tokutei
from mail import send_alert_email
from audio import record_chunk
from voice_alert import voice_alert

# --- 環境設定 ---
FORMAT = pyaudio.paInt16 # 2の補数として16bitで表現
CHANNELS = 1
RATE = 48000  # サンプリングレート (Hz) 1秒間に48000回電圧の変化を確認しにいっている
RECORD_SECONDS = 2 # 録音時間 (秒)
INTERVAL_SECONDS = 0.01  # 分析間隔 (秒)
CHUNK = 1024
# 閾値設定
THRESHOLD = 0.1 # 音量の最大値の閾値

# ★重要: ここをご自身の環境に合わせて書き換えてください
WHISPER_SERVER_PATH = "/home/name/tokushusagi/whisper.cpp/build/bin/whisper-server"
WHISPER_MODEL_PATH = "/home/name/tokushusagi/whisper.cpp/models/ggml-small.bin" # small推奨

def start_whisper_server():
    """ Whisperサーバーをバックグラウンドで起動する """
    print(f"Whisperサーバーを起動しています... (Model: {os.path.basename(WHISPER_MODEL_PATH)})")
    
    cmd = [
        WHISPER_SERVER_PATH,
        "-m", WHISPER_MODEL_PATH,
        "--port", "8080",
        "--host", "127.0.0.1",
        "-l", "ja",       # 日本語モード
        "-bs", "2",       # 高速化: 探索幅を1にする
        "-t", "4",        # CPUスレッド数: 8
        
    ]
    
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.DEVNULL, # デバッグ時は外してもOK
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(10) # モデルが大きい場合は読み込み時間を少し増やす
    print("Whisperサーバー起動完了 (PID: {})".format(process.pid))
    return process

def get_audio(stream, record_seconds):
    # 1秒間に含まれるデータ数
    total_frames = int(RATE * record_seconds)
    data = stream.read(total_frames, exception_on_overflow=False) # 16bit(2byte)*total_frames
    return data

def main():
    # 引数チェック（指定がなければ default モードにする）
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "default"
        
    print(f"'{mode}'モードで詐欺検知システムを起動します。")
    
    # 変数初期化
    audio = None
    stream = None
    server_process = None # プロセス変数の初期化

    try:
        # ★★★ 1. サーバー起動 ★★★
        server_process = start_whisper_server()

        # Audio初期化
        audio = pyaudio.PyAudio()
        
        # ストリームを開く
        stream = audio.open(
            format=FORMAT, 
            channels=CHANNELS, 
            rate=RATE, 
            input=True, 
            input_device_index=4, 
            frames_per_buffer=CHUNK # 適切なバッファサイズに変更
        )

        # --- 待機ループ（受話器が上がるのを待つ） ---
        print("待機中... (受話器が上がるのを検知します)")
        
        while True:
            data = get_audio(stream, 0.2)
            # この0.5秒でとる予定の物は捨てる（最初のいらない音を捨てる）
            result_list = zeroiti(data, RATE, INTERVAL_SECONDS, 0.7)
            
            # リストの中に1があるかどうか
            if 1 in result_list:
                print("初期微動計測: 反応あり")
                break
            else:
                pass

        # --- ナンバーディスプレイ解析 ---
        # 音声データを読み込む
        data = get_audio(stream, 2.3)
        result_list = zeroiti(data, RATE, 0.1, THRESHOLD)
        # ★家族フラグの初期化
        is_family = False
        
        if 10 <= countiti(result_list) <= 12:
            data = get_audio(stream, 1)
            # ナンバーディスプレイの信号があるかどうか判定
            result_list = zeroiti(data, RATE, INTERVAL_SECONDS, 0.10)
            index1, index2 = itinokazu(result_list)
            
            start_byte_index = (index1 + 1) * 2 * INTERVAL_SECONDS * RATE 
            end_byte_index = index2 * 2 * INTERVAL_SECONDS * RATE
            
        # インデックスチェック
            if index1 != -1 and end_byte_index > start_byte_index:
                data = data[int(start_byte_index):int(end_byte_index)]
                print("ナンバーディスプレイ信号検出")
                
                # バイナリデータをnp.int16の配列に変換し、正規化
                signal = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                print(f"{datetime.datetime.now()}: ナンバーディスプレイのパターンを検知しました。解析を開始します。")
                
                # デコード処理1
                decoded_data = decode_fsk(signal, 1200, 2100, 1300, 48000)
                decoded_bytes = decode_bytes(decoded_data)
                denwabangou1 = number_display(decoded_bytes)
                
                # デコード処理2 (少しずらして再試行)
                decoded_data2 = decode_fsk(signal[20:], 1200, 2100, 1300, 48000)
                decoded_bytes2 = decode_bytes(decoded_data2)
                denwabangou2 = number_display(decoded_bytes2)

                # 最後にまとめて、どちらかの番号が条件に合うかチェックします
                denwabangou = "05033333333"# ← 初期化（重要）
                
                # まず denwabangou1 をチェック
                if denwabangou1 and denwabangou1.isdigit() and len(denwabangou1) >= 10:
                    denwabangou = denwabangou1
                # denwabangou1 が条件に合わなければ、次に denwabangou2 をチェック
                elif denwabangou2 and denwabangou2.isdigit() and len(denwabangou2) >= 10:
                    denwabangou = denwabangou2
                
                # 値が代入されているかチェックしてから関数を呼ぶ
                if denwabangou is not None:
                    print(f"電話番号 {denwabangou} の調査を開始します...")
                    
                    # 戻り値を3つ受け取る (名前, 詳細テキスト, 危険フラグ)
                    owner_name, result_text, is_dangerous = tokutei(denwabangou)
                    
                    # 状況に応じて音声を出し分ける
                    if owner_name:
                        # ① 名前が登録されている場合（家族など）
                        msg = f"{owner_name}から電話です。"
                        print(f"【登録済】{msg}")
                        voice_alert(msg)

                        # ★家族フラグをONにする
                        print(">>> 家族・知人のため、詐欺判定機能とメール通知は停止します（文字起こしのみ実行） <<<")
                        is_family = True
                        
                    elif is_dangerous:
                        # ② 詐欺や迷惑電話の履歴がある場合
                        msg = "警告。この番号は迷惑電話の可能性があります。"
                        print(f"【警告】{msg}")
                        print(f"詳細: {result_text}")
                        voice_alert(msg)
                        
                        # 危険な場合はメールも送る
                        try:
                            send_alert_email() 
                        except Exception as e:
                            print(f"メール送信エラー: {e}")
                            
                    else:
                        # ③ 未登録で、かつ危険リストにもない場合
                        msg = "登録されていない番号からの電話です。注意してください。"
                        print(f"【不明】{msg}")
                        voice_alert(msg)
                else:
                    print("エラー: 電話番号が取得できませんでした。")
        
        # --- Whisper処理 (会話監視) ---  
        print(f"\n{datetime.datetime.now()}: リアルタイム監視を開始します。")
        full_history = "" # 会話の履歴を保存する変数
        
        while True:
            # audio.py 側でサーバー通信する record_chunk を呼ぶ
            text_chunk, is_finished = record_chunk(stream, duration=20)
            
            if text_chunk:
                full_history += text_chunk + " "
                print(f"\n--- 現在の会話ログ ---\n{full_history}\n----------------------")
                
                # ★変更点: 家族じゃない時だけ、LLM判定と警告を行う
                if not is_family:
                    # LLM判定
                    result = detect_fraud(full_history, mode)
                    
                    # 辞書型対策
                    if isinstance(result, dict):
                        result = json.dumps(result, ensure_ascii=False)
                    
                    print(f"LLM判定結果: {result}")

                    # --- 結果の解析 (正規表現) ---
                    match_prob = re.search(r"[\"']?fraud_probability[\"']?\s*[:]\s*(\d+)", result)
                    match_alert = re.search(r"[\"']?alert_level[\"']?\s*[:]\s*[\"']?(safe|warning|danger)[\"']?", result)

                    probability = 0
                    alert_lvl = "safe"

                    if match_prob:
                        probability = int(match_prob.group(1))
                    if match_alert:
                        alert_lvl = match_alert.group(1)

                    print(f"解析ステータス -> 危険度:{alert_lvl} (確率:{probability}%)")

                    # 判定結果に基づくアクション
                    if probability >= 80 or alert_lvl == "danger":
                        print("\n【緊急警告】詐欺の可能性が極めて高いです!警告メールを送信します!")
                        voice_alert("警告します。詐欺の可能性があります。注意してください。")
                        send_alert_email()
                        
                    elif alert_lvl == "warning":
                        print("【注意】: 少し怪しい要素が含まれていました。")
                        voice_alert("会話の内容に注意してください。")

                else:
                    # 家族の場合はここを通る（ログ出力のみ）
                    print("(家族のため詐欺判定はスキップ中...)")
                    
                # 通話終了（無音）ならループを抜ける
            if is_finished:
                print("通話が終了したため、監視を停止します。")
                break

    except KeyboardInterrupt:
        print("\n終了操作を受け付けました。")
    except Exception as e:
        print(f"予期せぬエラーが発生: {e}")
    
    finally:
        # ★★★ 2. 終了時にサーバーとストリームを確実に停止 ★★★
        print("システム終了処理中...")
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if audio is not None:
            audio.terminate()
            
        if server_process:
            print("Whisperサーバーを停止しています...")
            server_process.terminate()
            server_process.wait() # 完全に終了するまで待つ
            print("Whisperサーバー停止完了")
            
    print("システム終了")

if __name__ == "__main__":
    main()