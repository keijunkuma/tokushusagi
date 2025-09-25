# tokushusagi.py

# --- 標準ライブラリ ---
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
# --- 外部ライブラリ ---
from faster_whisper import WhisperModel
# --- 自作モジュール（ファイル）のインポート ---
from audio import record_and_transcribe 
from test import detect_fraud
from zeroitihantei import zeroiti, interval
from phonenumber import number_display, print_bytes, decode_fsk, decode_bytes
from bbb import itinokazu,countiti
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

def get_audio(stream,record_seconds):
    # 1秒間に含まれるデータ数
    total_frames = int(RATE * record_seconds)
    data = stream.read(total_frames, exception_on_overflow=False) #16bit(2byte)*total_frames
    return data

def main():
    mode = sys.argv[1]
    print(f"'{mode}'モードで詐欺検知システムを起動します。")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=4, frames_per_buffer=CHUNK) #48000hzごとにformatで録音

    while True :
        data = get_audio(stream, 0.2)
        #この0.5秒でとる予定の物は捨てる最初のいらない音を捨てる
        result_list = zeroiti(data, RATE, INTERVAL_SECONDS, THRESHOLD)
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
            number_display(decoded_bytes)
            print("ddd")
            # デコード処理を実行
            decoded_data = decode_fsk(signal[20:], 1200, 2100, 1300, 48000)
            print(decoded_data)
            decoded_bytes = decode_bytes(decoded_data)
            print_bytes(decoded_bytes)
            number_display(decoded_bytes)
            print("ddd")

    #whisper処理  
    print(f"{datetime.datetime.now()}: 文字起こしをします。")
    transcription = record_and_transcribe(mode,stream)
    
    
    if transcription:
        print("\n---最終的な文字起こし結果---")
        print(transcription)
        print("--------------------------\n")

        result = detect_fraud(transcription, mode)

        match = re.search(r'詐欺の確率(\d+)%', result)
        if match:
            probability = int(match.group(1))
            print(f"詐欺の確率部分: {probability}%")
            if probability >= 70:
                print("【警告】: 詐欺の可能性が非常に高いです")
                # 必要に応じてメール送信を実行
                send_alert_email()
            else:
                print("詐欺の可能性は低いです")
        else:
            print("判定結果から確率を読み取れませんでした。")
    else:
        print("文字起こしされたテキストがありません。")

if __name__ == "__main__":
    main()
    
