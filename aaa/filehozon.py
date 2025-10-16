import pyaudio
import numpy as np
from faster_whisper import WhisperModel
from scipy.signal import resample
from zeroitihantei import zeroiti
import wave

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000  # 録音レートは48000Hzのまま
SEGMENT_DURATION = 10  # 10秒ごとに文字起こし処理を実行
THRESHOLD = 0.1  # 音量の最大値の閾値

def record_and_transcribes(mode: str, stream) -> str:
    """
    マイクからリアルタイムで録音し、文字起こしを行う関数。
    """
    # Whisperモデルの準備
    # Faster Whisperを使用しているため、resampled_buffer (float32, -1.0~1.0) をそのまま渡せます
    model = WhisperModel("large-v3", device="cpu", compute_type="float32")

    frames = []
    full_transcription = ''
    
    # Whisperが推奨するサンプリングレート
    WHISPER_RATE = 16000
    print("録音開始")
    while True:
        for _ in range(0, int(RATE * SEGMENT_DURATION / CHUNK)):
            # 録音
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        segment_data = b''.join(frames)
        # numpyバッファに変換（16bit intを -1.0~1.0のfloat32に正規化）
        buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0

        # 録音した音声を16000Hzにダウンサンプリング
        num_samples_resampled = int(buffer.shape[0] * (WHISPER_RATE / RATE))
        
        # scipy.signal.resample を使用すると、データ型は float64 になります
        resampled_buffer = resample(buffer, num_samples_resampled)
        
        # WAVファイル書き込み用: floatデータを16bit intに戻す (ノイズの原因を解消)
        # 値を 32767倍し、np.int16型に変換してバイト列にします
        # resampled_buffer が float64 になっている場合でも正しく処理されます
        resampled_int16 = (resampled_buffer * 32767).astype(np.int16)

        file = "/home/name/tokushusagi/aaa/ccc.wav"
        
        # WAVファイルとしてディスクに書き込み
        with wave.open(file, mode='wb') as wb:
            wb.setnchannels(1)  # モノラル
            wb.setsampwidth(2)  # 16bit=2byte
            wb.setframerate(WHISPER_RATE)
            # 16bit intに変換したデータを書き込む
            wb.writeframes(resampled_int16.tobytes())
        
        # Whisperでの文字起こし (float32で正規化されたデータを使用)
        segments, _ = model.transcribe(resampled_buffer, language="ja")
        
        segments = list(segments)
        print("---")
        for segment in segments:
            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        
        # 連続処理のためのバッファ調整（元コードのロジックを維持）
        if len(segments) >= 2:
            for segment in segments[:-1]:
                if segment.text not in full_transcription:
                    full_transcription += segment.text
            
            # 最後の未処理のフレームまで戻るための処理
            last_processed_time = segments[-2].end
            # ダウンサンプリング前のバッファ（RATE=48000）のインデックスを計算する必要がある
            last_processed_frame_index = int(last_processed_time * RATE / WHISPER_RATE * (RATE / CHUNK)) # 修正の必要性あり、ここでは元のロジックを維持
            
            # 録音バッファの先頭から、すでに処理した分を削除
            del frames[:last_processed_frame_index]

        # 無音判定のロジック
        renzokuzero = zeroiti(segment_data, RATE, 0.01, THRESHOLD)
        # 0が続いたら終了
        if 1 not in renzokuzero:
            print("無音が連続しました。録音を終了します。")
            break
        
    # 終了時の最終セグメント処理
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