from zeroitihantei import zeroiti 
import pyaudio

FORMAT = pyaudio.paInt16 # 2の補数として16bitで表現
CHANNELS = 1
RATE = 48000  # サンプリングレート (Hz) 1秒間に48000回電圧の変化を確認しにいっている
RECORD_SECONDS = 2 # 録音時間 (秒)
INTERVAL_SECONDS = 0.01  # 分析間隔 (秒)
CHUNK = 1024
# 閾値設定
THRESHOLD = 0.1 # 音量の最大値の閾値

def get_audio(stream, record_seconds):
    # 1秒間に含まれるデータ数
    total_frames = int(RATE * record_seconds)
    data = stream.read(total_frames, exception_on_overflow=False) # 16bit(2byte)*total_frames
    return data


# Audio初期化
audio = pyaudio.PyAudio()

# ストリームを開く
stream = audio.open(
    format=FORMAT, 
    channels=CHANNELS, 
    rate=RATE, 
    input=True, 
    input_device_index=0, 
    frames_per_buffer=CHUNK # 適切なバッファサイズに変更
)
while True:

    data = get_audio(stream, 0.5)
    # この0.5秒でとる予定の物は捨てる（最初のいらない音を捨てる）
    result_list = zeroiti(data, RATE, INTERVAL_SECONDS, 0.1)
    
    # リストの中に1があるかどうか
    print(sum(result_list))
    if sum(result_list) > 10:
        print("初期微動計測: 反応あり")
    else:
        pass