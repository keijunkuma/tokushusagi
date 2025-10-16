import pyaudio
import wave

# --- 録音設定 ---
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 10
WAVE_OUTPUT_FILENAME = "recording1.wav"

p = pyaudio.PyAudio()

# p.open() から 'exception_on_overflow' を削除
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=4)

print("🎙️  録音中...")

frames = []

# ループ内の stream.read() でオーバーフローを処理
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    try:
        # 💡 解決策: stream.read() に引数を追加
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    except IOError as e:
        print(f"録音中にエラーが発生しました: {e}")
        # エラーが発生した場合でも、それまでに録音したデータを保存するためにループを抜ける
        break


print("✅  録音終了。")

# ストリームを停止・終了
stream.stop_stream()
stream.close()
p.terminate()

# 録音が終わってからファイルに保存
with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))

print(f"ファイルが '{WAVE_OUTPUT_FILENAME}' として保存されました。")