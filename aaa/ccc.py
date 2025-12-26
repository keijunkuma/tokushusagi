import pyaudio

audio = pyaudio.PyAudio()
print("--- デバイス一覧 ---")
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    # 入力デバイス（マイク）だけを表示
    if info['maxInputChannels'] > 0:
        print(f"Index {i}: {info['name']}")

audio.terminate()