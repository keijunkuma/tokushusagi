# audio_handler.py

import pyaudio
import numpy as np
from faster_whisper import WhisperModel

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
SEGMENT_DURATION = 10  # 10秒ごとに文字起こし処理を実行

# modelを引数として受け取るように変更
def record_and_transcribe(mode:str) -> str:
    """
    マイクからリアルタイムで録音し、文字起こしを行う関数。
    """
    # Whisperモデルの準備 (これはメインのプログラムが持つ)
    if mode == 'local':
        model = WhisperModel("large-v3", device="cpu", compute_type="float16")
    else:
        model = WhisperModel("large-v3", device="cuda", compute_type="float16")


    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("録音開始... (Ctrl+Cで終了)")

    frames = []
    full_transcription = ''

    try:
        while True:
            for _ in range(0, int(RATE * SEGMENT_DURATION / CHUNK)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            segment_data = b''.join(frames)
            buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0

            segments, _ = model.transcribe(buffer, language="ja")
            
            segments = list(segments)
            print("---")
            for segment in segments:
                print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            
            if len(segments) >= 2:
                for segment in segments[:-1]:
                    if segment.text not in full_transcription:
                        full_transcription += segment.text
                
                last_processed_time = segments[-2].end
                last_processed_frame_index = int(last_processed_time * RATE / CHUNK)
                del frames[:last_processed_frame_index]

    except KeyboardInterrupt:
        print("\n録音を終了します。最終処理中...")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
    
    if frames:
        segment_data = b''.join(frames)
        buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = model.transcribe(buffer, language="ja")
        for segment in segments:
            if segment.text not in full_transcription:
                full_transcription += segment.text

    return full_transcription

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("使用法: python audio_handler.py <mode>")
        sys.exit(1)
    mode = sys.argv[1]
    transcription = record_and_transcribe(mode)
    print("\n---最終的な文字起こし結果---")
    print(transcription)
    print("--------------------------\n")
    