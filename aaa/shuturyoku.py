import pyaudio
import numpy as np
import time

# ★まずは Index 3 (Analog) を試す
OUTPUT_INDEX = 5
# もしこれでダメなら、次は 4 (USB Audio) に書き換えて試してください

RATE = 44100
DURATION = 2  # 2秒鳴らす

def play_tone():
    p = pyaudio.PyAudio()
    
    print(f"Index {OUTPUT_INDEX} でテスト音声を再生します...")

    # "プー"という音（サイン波）を作る
    frequency = 440.0  # 440Hz (ラ)
    t = np.linspace(0, DURATION, int(RATE * DURATION), False)
    # 音量(0.5)
    tone = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    # float32 -> int16変換
    audio_data = (tone * 32767).astype(np.int16).tobytes()

    try:
        # チャンネル数は安全策で 1 (モノラル) に設定
        stream = p.open(format=pyaudio.paInt16,
                        channels=1, 
                        rate=RATE,
                        output=True,
                        output_device_index=OUTPUT_INDEX)
        
        stream.write(audio_data)
        time.sleep(0.5) # 再生待ち
        
        stream.stop_stream()
        stream.close()
        print("再生完了しました。音が聞こえましたか？")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("ヒント: デバイスが使用中(Busy)か、対応していない設定の可能性があります。")
    finally:
        p.terminate()

if __name__ == "__main__":
    play_tone()