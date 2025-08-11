from pickle import TRUE
import os
import wave
import pyaudio
from faster_whisper import WhisperModel
import requests
import json
import re
import smtplib
from email.mime.text import MIMEText
import ssl
import numpy as np
import datetime
import base64
import os
from google import genai
from google.genai import types

# 環境変数の読み込み
SMTP_SERVER = os.getenv('SMTP_SERVER')
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL')
SMTP_PASS = os.getenv('SMTP_PASS')
key = ""

# Whisperモデルの準備
#model = WhisperModel("/content/large-v3-turbo-ct2", device="cpu", compute_type="int8", local_files_only=True)
model = WhisperModel("large-v3-turbo", device="cuda", compute_type="int8", local_files_only=False)

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
SEGMENT_DURATION = 10  # 5秒ごとに録音
TOTAL_DURATION = 60   # 合計録音時間（例：60秒）

DUMMY = True

# 録音 + 文字起こし（ファイルを保存せず、bytesを結合）
def record_and_transcribe():
    audio = pyaudio.PyAudio()
    if DUMMY:
      stream = wave.open("0e874dc23542d17e635d73547b245bb0.wav","r")
    else:
      stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("録音開始...")


    transcription = ''
    #前の段階の処理が入るようになっているのでframes = []をfor文の中に入れることができない
    frames = []

    i = 0

    while True:
      i = i+1
      print(f"録音中... {i * SEGMENT_DURATION} 秒目")
      print(frames)


      fuetenai = True
      #chunkを細かくすることで、下のコードで最後のブロック以外を消せるようにしている
      for _ in range(0, int(RATE * SEGMENT_DURATION / CHUNK)):
        if DUMMY:
          data = stream.readframes(CHUNK)
        else:
          data = stream.read(CHUNK, exception_on_overflow=False)
        if len(data) != 0:
          frames.append(data)
          #この部分にbreakを入れないのは今回の処理になにも入っていないとき、ここで終わらせると前段階の最後のブロックのデータが処理されずに消えてしまうから
          fuetenai = False

      segment_data = b''.join(frames)
      print(type(segment_data))
      buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32)/32768.0
      #transcribeに入れられる形式標本化周波数　= 16000Hz 量子化＝float32　符号化　＝float
      segments, _ = model.transcribe(buffer, "ja")
      print(datetime.datetime.now())
      segments =list(segments)
      for segment in segments:
        print(segment)

      print(datetime.datetime.now())

      if len(segments) >= 2:
        for segment in segments[:-1]:
          transcription += segment.text + '\n'
          print(transcription)

        segment = segments[-2]  # 最後から2番目
        aaa = float(segment.end)
        bbb = int(aaa * RATE // CHUNK)
        print(bbb)
        del frames[0:bbb]

      elif fuetenai == True:
        for segment in segments:
          transcription += segment.text + '\n'
          print(transcription)
        break

      print(frames)
      print(len(frames))

    if DUMMY:
      stream.close()
    else:
      stream.stop_stream()
      stream.close()
      audio.terminate()

    return transcription

# 詐欺判定APIとの通信
def detect_fraud(transcription):
    client = genai.Client(
        api_key=key,
    )

    model = "gemma-3-1b-it"
    contents = [
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""今から文字列を送るので詐欺か詐欺ではないかだけで判断してください。出力例に完全に一致するように出してください。\\n### 出力例\\n詐欺の確率100%"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=transcription),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
    )

    ret = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
      for candidate in chunk.candidates:
        if candidate.finish_reason == None:
          for part in candidate.content.parts:
            ret = ret + part.text
            #print(part.text)
    print(ret)
    return ret

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

# メイン処理
def main():
    transcription = record_and_transcribe()
    result = detect_fraud(transcription)

    match = re.search(r'詐欺の確率(\d+)%', result)
    if match:
        probability = int(match.group(1))
        print(f"詐欺の確率部分: {probability}%")
        if probability >= 70:
            print("詐欺の可能性が高いです")
            #send_alert_email()
        else:
            print("詐欺の可能性は低いです")
    else:
        print("該当する部分はありません")

if __name__ == "__main__":
    main()
