import requests
import json
from faster_whisper import WhisperModel
import re
import pyaudio
import wave
import smtplib
from email.mime.text import MIMEText
import ssl

SMTP_SERVER = os.getenv('SMTP_SERVER')
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL')
SMTP_PASS = os.getenv('SMTP_PASS')

def MakeWavFile(FileName="sample.wav", Record_Seconds=2):
    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()
    
    stream = p.open(format=FORMAT,
                    channels=1,
                    rate=RATE,
                    input=True,
                    input_device_index = 1,
                    frames_per_buffer=chunk)
    
    # レコード開始
    print("Now Recording...")
    all = []
    for i in range(0, int(RATE / chunk * Record_Seconds)):
        data = stream.read(chunk, exception_on_overflow = False)  # 音声を読み取って、
        all.append(data)  # データを追加
    
    # レコード終了
    print("Finished Recording.")
    
    stream.close()
    p.terminate()
    wavFile = wave.open(FileName, 'wb')  # 引数でファイル名を渡す
    wavFile.setnchannels(CHANNELS)
    wavFile.setsampwidth(p.get_sample_size(FORMAT))
    wavFile.setframerate(RATE)
    wavFile.writeframes(b''.join(all))  # Python2 用
    # wavFile.writeframes(b"".join(all)) # Python3用
    
    wavFile.close()

    
# WAVファイル作成, 引数は（ファイル名, 録音する秒数）
MakeWavFile("sample.wav", Record_Seconds=30)

# model = WhisperModel("large-v3", device="cpu", compute_type="int8", local_files_only=False)  # GPUを使用する場合は "cuda" を指定
model = WhisperModel("./medium", device="cpu", compute_type="int8", local_files_only=False)  # GPUを使用する場合は "cuda" を指定

audio_path = "sample.wav"
segments, _ = model.transcribe(audio_path, language="ja")

transcription = ''
for segment in segments:
   transcription += str(segment.text) + '\n'
print(transcription)

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
fraud_probability = j['choices'][0]['message']['content']
# fraud_probability =  "詐欺の確率0%\n詐欺の確率1%\n詐欺の確率2%\nこれは100%詐欺ではありません"
print(fraud_probability)

# 改行以降の数字と % を取得
match = re.search(r'詐欺の確率(\d+)%', fraud_probability)

if match:
    # 詐欺の確率を整数として取得
    print(match.group(1))
    probability = int(match.group(1))
    print(f"詐欺の確率部分: {probability}%")
    # 詐欺の可能性が高いかどうか判断
    if probability >= 70:
        print("詐欺の可能性が高いです")
        # メール送信部分
        msg = MIMEText("詐欺の確率が高いです、確認をとってみてください", "plain", "utf-8")
        msg['Subject'] = "鳥の便り_詐欺対策サービス"
        msg['From'] = FROM_EMAIL
        msg['To'] = TO_EMAIL

        context = ssl.create_default_context()
        smtpobj = smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context)
        smtpobj.login(FROM_EMAIL, SMTP_PASS)
        smtpobj.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        smtpobj.quit()

    elif probability < 70:
        print("詐欺の可能性は低いです")
else:
    print("該当する部分はありません")