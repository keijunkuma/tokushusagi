import os
import wave
import pyaudio
import time
from faster_whisper import WhisperModel
import requests
import json
import re
import smtplib
from email.mime.text import MIMEText
import ssl

# 環境変数の読み込み
SMTP_SERVER = os.getenv('SMTP_SERVER')
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL')
SMTP_PASS = os.getenv('SMTP_PASS')

# Whisperモデルの準備
model = WhisperModel("./medium", device="cpu", compute_type="int8", local_files_only=False)

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
SEGMENT_DURATION = 5  # 5秒ごとに録音
TOTAL_DURATION = 60   # 合計録音時間（例：60秒）

# 録音 + 逐次文字起こし
def record_and_transcribe():
    transcription = ''
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)
    
    print("録音開始...")

    for i in range(0, TOTAL_DURATION, SEGMENT_DURATION):
        frames = []
        print(f"録音中... {i + SEGMENT_DURATION} 秒目")

        for _ in range(0, int(RATE / CHUNK * SEGMENT_DURATION)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        # 一時的なファイル名で保存
        filename = f"segment_{i}.wav"
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # 文字起こし
        segments, _ = model.transcribe(filename, language="ja")
        for segment in segments:
            transcription += segment.text + '\n'

        os.remove(filename)  # 一時ファイル削除

    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    print("録音完了。")
    return transcription


# 詐欺判定APIとの通信
def detect_fraud(transcription):
    url = "http://localhost:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": "今から文字列を送るので詐欺か詐欺ではないかだけで判断してください。出力例に完全に一致するように出してください。\n### 出力例\n詐欺の確率100%"
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    j = response.json()
    result = j['choices'][0]['message']['content']
    print(result)
    return result


# メール送信
def send_alert_email():
    msg = MIMEText("詐欺の確率が高いです、確認をとってみてください", "plain", "utf-8")
    msg['Subject'] = "鳥の便り_詐欺対策サービス"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    context = ssl.create_default_context()
    smtpobj = smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context)
    smtpobj.login(FROM_EMAIL, SMTP_PASS)
    smtpobj.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
    smtpobj.quit()
    print("メールを送信しました。")


def main():
    # 録音 + テキスト化
    transcription = record_and_transcribe()

    # 詐欺判定
    result = detect_fraud(transcription)
    match = re.search(r'詐欺の確率(\d+)%', result)

    if match:
        probability = int(match.group(1))
        print(f"詐欺の確率部分: {probability}%")

        if probability >= 70:
            print("詐欺の可能性が高いです")
            send_alert_email()
        else:
            print("詐欺の可能性は低いです")
    else:
        print("該当する部分はありません")


if __name__ == "__main__":
    main()