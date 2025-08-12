# tokushusagi.py

# --- 標準ライブラリ ---
import sys
import os
import re
import smtplib
from email.mime.text import MIMEText
import ssl
import datetime

# --- 外部ライブラリ ---
import pyaudio
import numpy as np
from faster_whisper import WhisperModel

# --- ここが「切り替えスイッチ」の核心部分 ---
if len(sys.argv) < 2 or sys.argv[1] not in ['local', 'cloud']:
    print("エラー: 実行モードを指定してください。")
    print("使い方: python tokushusagi.py local または python tokushusagi.py cloud")
    sys.exit(1)

mode = sys.argv[1]

# 引数に応じて、どちらのdetect_fraud関数をインポートするか決める
if mode == 'local':
    from my_local_ai.py import detect_fraud
else: # mode == 'cloud'
    from my_cloud_ai.py import detect_fraud
# --- スイッチここまで ---


# 環境変数の読み込み (メール送信用)
SMTP_SERVER = os.getenv('SMTP_SERVER')
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL')
SMTP_PASS = os.getenv('SMTP_PASS')

# Whisperモデルの準備
# ご自身の環境に合わせてモデルや設定を調整してください
# 例: CPUで動かす場合 -> device="cpu", compute_type="int8"
model = WhisperModel("large-v3", device="cuda", compute_type="float16")

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
SEGMENT_DURATION = 10  # 10秒ごとに文字起こし処理を実行

def record_and_transcribe():
    """
    マイクからリアルタイムで録音し、文字起こしを行う関数。
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("録音開始... (Ctrl+Cで終了)")

    frames = []
    full_transcription = ''

    try:
        while True:
            # SEGMENT_DURATION秒分の音声データを録音
            for _ in range(0, int(RATE * SEGMENT_DURATION / CHUNK)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            # 現在の音声バッファをNumpy配列に変換
            segment_data = b''.join(frames)
            buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0

            # 文字起こしを実行
            segments, _ = model.transcribe(buffer, language="ja")
            
            segments = list(segments)
            print("---") # 区切り線
            for segment in segments:
                print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            
            # 最後のセグメントが不完全な可能性があるため、それ以外を確定させる
            if len(segments) >= 2:
                # 処理済みのテキストを結合
                for segment in segments[:-1]:
                    # 重複を避けるため、確定済みテキストに含まれていない部分のみ追加
                    if segment.text not in full_transcription:
                         full_transcription += segment.text
                
                # 処理済みのオーディオデータをバッファから削除 (スライディングウィンドウ)
                last_processed_time = segments[-2].end
                last_processed_frame_index = int(last_processed_time * RATE / CHUNK)
                del frames[:last_processed_frame_index]

    except KeyboardInterrupt:
        print("\n録音を終了します。最終処理中...")
    finally:
        # ストリームを安全に停止・終了
        stream.stop_stream()
        stream.close()
        audio.terminate()
    
    # ループ終了後、バッファに残っている音声を最後の文字起こし
    if frames:
        segment_data = b''.join(frames)
        buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = model.transcribe(buffer, language="ja")
        for segment in segments:
             if segment.text not in full_transcription:
                  full_transcription += segment.text

    return full_transcription

def send_alert_email():
    """
    詐欺の可能性が高い場合に警告メールを送信する関数。
    """
    # メール情報が設定されているか確認
    if not all([SMTP_SERVER, FROM_EMAIL, TO_EMAIL, SMTP_PASS]):
        print("警告: メールの環境変数が設定されていないため、メールは送信されません。")
        return

    msg = MIMEText("詐欺の確率が高い会話が検知されました。本人に確認を取るなど、ご注意ください。", "plain", "utf-8")
    msg['Subject'] = "【重要・詐欺警告】鳥の便り リアルタイム検知サービス"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    print("警告メールを送信しています...")
    try:
        context = ssl.create_default_context()
        smtpobj = smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context)
        smtpobj.login(FROM_EMAIL, SMTP_PASS)
        smtpobj.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        smtpobj.quit()
        print("メールを送信しました。")
    except Exception as e:
        print(f"メールの送信に失敗しました: {e}")

def main():
    print(f"'{mode}'モードで詐欺検知システムを起動します。")
    transcription = record_and_transcribe()
    
    if transcription:
        print("\n---最終的な文字起こし結果---")
        print(transcription)
        print("--------------------------\n")

        # ここで呼び出すdetect_fraudは、起動時の引数によって中身が変わっている
        result = detect_fraud(transcription)

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