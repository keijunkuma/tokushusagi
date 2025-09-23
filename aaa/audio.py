import pyaudio
import numpy as np
from faster_whisper import WhisperModel
from scipy.signal import resample
from zeroitihantei import zeroiti
from zero import has_thirty_consecutive_zeros

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000  # 録音レートは48000Hzのまま
SEGMENT_DURATION = 10  # 10秒ごとに文字起こし処理を実行
THRESHOLD = 0.1  # 音量の最大値の閾値

def record_and_transcribe(mode: str, stream) -> str:
    """
    マイクからリアルタイムで録音し、文字起こしを行う関数。
    """
    # Whisperモデルの準備
    model = WhisperModel("large-v3", device="cpu", compute_type="float16")

    frames = []
    full_transcription = ''
    
    # Whisperが推奨するサンプリングレート
    WHISPER_RATE = 16000

    while True:
        for _ in range(0, int(RATE * SEGMENT_DURATION / CHUNK)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        segment_data = b''.join(frames)
        # numpyバッファに変換
        buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0

        # 録音した音声を16000Hzにダウンサンプリング
        num_samples_resampled = int(buffer.shape[0] * (WHISPER_RATE / RATE))
        resampled_buffer = resample(buffer, num_samples_resampled)
        
        segments, _ = model.transcribe(resampled_buffer, language="ja")
        
        segments = list(segments)
        print("---")
        for segment in segments:
            # タイムスタンプはダウンサンプリング後の時間で表示される
            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        
        if len(segments) >= 2:
            for segment in segments[:-1]:
                if segment.text not in full_transcription:
                    full_transcription += segment.text
            
            # 最後の未処理のフレームまで戻る
            last_processed_time = segments[-2].end
            last_processed_frame_index = int(last_processed_time * RATE / WHISPER_RATE * CHUNK)
            
            # 録音バッファの先頭から、すでに処理した分を削除
            del frames[:last_processed_frame_index]

        renzokuzero = zeroiti(segment_data, RATE, 0.01, THRESHOLD)
        if all(0 == renzokuzero[0] for 0 in renzokuzero) == True:
            print("無音が連続しました。録音を終了します。")
            break
        
    if frames:
        segment_data = b''.join(frames)
        buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # 最終セグメントもリサンプリング
        num_samples_resampled = int(buffer.shape[0] * (WHISPER_RATE / RATE))
        resampled_buffer = resample(buffer, num_samples_resampled)
        
        segments, _ = model.transcribe(resampled_buffer, language="ja")
        for segment in segments:
            if segment.text not in full_transcription:
                full_transcription += segment.text

    return full_transcription

if __name__ == "__main__":
    import sys
    
    # scipyがインストールされているか確認
    try:
        import scipy
    except ImportError:
        print("scipyライブラリが必要です。`pip install scipy` でインストールしてください。")
        sys.exit(1)

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("録音開始... (Ctrl+Cで終了)")

    if len(sys.argv) != 2:
        print("使用法: python audio_handler.py <mode>")
        sys.exit(1)
    
    mode = sys.argv[1]
    transcription = record_and_transcribe(mode, stream)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    print("\n---最終的な文字起こし結果---")
    print(transcription)
    print("--------------------------\n")
    