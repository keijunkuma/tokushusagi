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
# --- 外部ライブラリ ---
from faster_whisper import WhisperModel
# --- 自作モジュール（ファイル）のインポート ---
from audio import record_and_transcribe 
from test import detect_fraud
from zeroitihantei import zeroiti, hantei
from phonenumber import number_display, print_bytes, decode_fsk, decode_bytes
# --- 環境変数の読み込み ---
# --- ここまで ---

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000  # サンプリングレート (Hz)
RECORD_SECONDS = 2 # 録音時間 (秒)
INTERVAL_SECONDS = 0.01  # 分析間隔 (秒)
CHUNK = 1024
# 閾値設定
THRESHOLD = 0.1  # 音量の最大値の閾値
# 1秒間に含まれるデータ数
total_frames = int(RATE * RECORD_SECONDS)


# 環境変数の読み込み (メール送信用)
SMTP_SERVER = os.getenv('SMTP_SERVER')
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL')
SMTP_PASS = os.getenv('SMTP_PASS')


#【ここを修正】send_alert_email関数の中身を元に戻す
def send_alert_email():
    """
    詐欺の可能性が高い場合に警告メールを送信する関数。
    """
    # メール情報が環境変数に設定されているか確認
    if not all([SMTP_SERVER, FROM_EMAIL, TO_EMAIL, SMTP_PASS]):
        print("警告: メールの環境変数が設定されていないため、メールは送信されません。")
        return

    # メールの内容を作成
    msg = MIMEText("詐欺の確率が高い会話が検知されました。本人に確認を取るなど、ご注意ください。", "plain", "utf-8")
    msg['Subject'] = "【重要・詐欺警告】鳥の便り リアルタイム検知サービス"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    print("警告メールを送信しています...")
    try:
        # メールサーバーに接続して送信
        context = ssl.create_default_context()
        smtpobj = smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context)
        smtpobj.login(FROM_EMAIL, SMTP_PASS)
        smtpobj.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        smtpobj.quit()
        print("メールを送信しました。")
    except Exception as e:
        print(f"メールの送信に失敗しました: {e}")

def main():
    mode = sys.argv[1]
    print(f"'{mode}'モードで詐欺検知システムを起動します。")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)


    while True:
    # 音声データを読み込む
        data = stream.read(total_frames, exception_on_overflow=False)

        result_list = zeroiti(data, RATE, INTERVAL_SECONDS, THRESHOLD)

        result = hantei(result_list)
        if result == True:
            print(f"{datetime.datetime.now()}: 詐欺の可能性が高いパターンを検知しました。文字起こしと判定を開始します。")
            break
        else:
            print(f"{datetime.datetime.now()}: 詐欺の可能性は低いと判断されました。再度音声を取得します。")
    
    _, signal = data
    signal = signal / 32768.0  # Normalize
    decoded_data = decode_fsk(signal[8:], 1200, 2100, 1300, 48000)
    print(decoded_data)
    decoded_bytes = decode_bytes(decoded_data)
    print_bytes(decoded_bytes)
    number_display(decoded_bytes)
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
    
