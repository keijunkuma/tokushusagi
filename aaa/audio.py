import pyaudio
import numpy as np
from faster_whisper import WhisperModel
from scipy.signal import resample
# zeroitihantei.pyファイルが別途必要です
# 無音検出に使用されるため、このimportは維持します
from zeroitihantei import zeroiti

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000  # 録音レートは48000Hzのまま
SEGMENT_DURATION = 10  # 10秒ごとに文字起こし処理を実行
THRESHOLD = 0.1  # 音量の最大値の閾値

def record_and_transcribe(stream) -> str:
    """
    マイクからリアルタイムで録音し、3倍速処理で文字起こしを行う関数。
    """
    # Whisperモデルの準備
    # CPUでの実行は非常に時間がかかるため、GPUがあればdevice="cuda"を推奨します。
    model = WhisperModel("large-v3", device="cpu", compute_type="float32")

    frames = []
    full_transcription = ''

    # Whisperが推奨するサンプリングレート
    WHISPER_RATE = 16000

    # --- 3倍速処理のための固定設定 ---
    speed_factor = 3.0
    # Whisperに「3倍速で録音された音声」だと認識させるための偽のサンプリングレート
    fake_sample_rate = int(RATE * speed_factor)
    print(f"🚀 高速化モード: Whisperに {fake_sample_rate}Hz の音声として渡します (実質3倍速処理)")
    # --------------------------

    while True:
        # 10秒分のフレームを録音
        # 注意: 実際に録音される実時間はSEGMENT_DURATION (10秒) です
        for _ in range(0, int(RATE * SEGMENT_DURATION / CHUNK)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        segment_data = b''.join(frames)
        # numpyバッファに変換
        buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0

        # --- 3倍速: サンプリングレートを偽装して渡す ---
        segments, _ = model.transcribe(
            buffer,
            language="ja",
            initial_prompt="ご提供いただいた音声を、以下の通りに文字起こしします。",
            vad_filter=True,
            sample_rate=fake_sample_rate # <--- 3倍速化の肝
        )
        # -----------------------------------------------

        segments = list(segments)
        print("---")
        # タイムスタンプは偽装されたレートに基づく時間です (実時間ではない)
        for segment in segments:
            # 実際の時間は segment.start / speed_factor で計算できます
            print(f"[偽装時間: {segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

        # リアルタイム処理ロジック
        if len(segments) >= 2:
            for segment in segments[:-1]:
                if segment.text not in full_transcription:
                    full_transcription += segment.text

            # 最後の未処理のフレームまで戻る (バッファ削除)
            last_processed_time = segments[-2].end

            # 偽装された時間 (3x) を実際の処理時間 (1x) に戻す
            actual_processed_time = last_processed_time / speed_factor

            # 実際の処理時間から、48000Hzの元のフレームのインデックスを計算
            last_processed_frame_index = int(actual_processed_time * WHISPER_RATE / (RATE / CHUNK)) * CHUNK

            # 録音バッファの先頭から、すでに処理した分を削除
            del frames[:last_processed_frame_index]

        # 無音判定ロジック
        renzokuzero = zeroiti(segment_data, RATE, 0.01, THRESHOLD)
        if 1 not in renzokuzero:
            print("無音が連続しました。録音を終了します。")
            break

    # 最終セグメントの処理
    if frames:
        segment_data = b''.join(frames)
        buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0

        num_samples_resampled = int(buffer.shape[0] * (WHISPER_RATE / RATE))
        resampled_buffer = resample(buffer, num_samples_resampled)

        segments, _ = model.transcribe(
            resampled_buffer,
            language="ja",
            sample_rate=fake_sample_rate # <--- ここでも偽装レートを渡す
        )
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
    print("本コードは3倍速処理で固定されています。")

    # mode引数のチェックを削除し、直接関数を呼び出し
    transcription = record_and_transcribe(stream)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    print("\n---最終的な文字起こし結果 (3倍速処理)---")
    print(transcription)
    print("----------------------------------------\n")