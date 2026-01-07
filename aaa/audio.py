import pyaudio
import numpy as np
import subprocess
import wave
import tempfile
import os
import sys
from scipy.signal import resample

# main.pyから呼ばれる zeroitihantei をインポート
try:
    from zeroitihantei import zeroiti
except ImportError:
    zeroiti = None

# --- 設定 ---
WHISPER_CLI_PATH = "/home/name/tokushusagi/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL_PATH = "/home/name/tokushusagi/whisper.cpp/models/ggml-base.bin"

# 録音設定
CHUNK = 1024
RATE = 48000
THRESHOLD = 0.1

def transcribe_with_cli(audio_data_48k):
    """ 音声データをGPU版Whisperで文字起こしする """
    try:
        # 1. 前処理 (48kHz -> 16kHz)
        audio_np = np.frombuffer(audio_data_48k, dtype=np.int16).astype(np.float32) / 32768.0
        num_samples_target = int(len(audio_np) * 16000 / RATE)
        resampled_audio = resample(audio_np, num_samples_target)
        resampled_int16 = (resampled_audio * 32768.0).astype(np.int16)

        # 2. 一時ファイル保存
        # ★ここで i を使うとエラーになるので、tempfileにお任せしています
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_filename = temp_wav.name
        
        with wave.open(temp_filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(resampled_int16.tobytes())

        # 3. Whisper実行
        cmd = [
            WHISPER_CLI_PATH,
            "-m", WHISPER_MODEL_PATH,
            "-f", temp_filename,
            "-l", "ja",
            "--no-timestamps"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        text = result.stdout.strip()
        
        return text

    except Exception as e:
        print(f"Whisperエラー: {e}")
        return ""
    finally:
        # 一時ファイルの削除
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)

def record_chunk(stream, duration=20):
    """
    指定した秒数(duration)だけ録音して、テキストと「通話終了フラグ」を返す
    """
    print(f"録音中({duration}秒)...")
    frames = []
    
    # ★修正1: 1秒あたり何チャンクか計算しておく
    chunks_per_sec = int(RATE / CHUNK)

    # ★修正2: ループ変数を '_' から 'i' に変更
    for i in range(0, int(RATE * duration / CHUNK)):
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

            # ログ表示用 (1秒ごとに表示)
            if (i + 1) % chunks_per_sec == 0:
                current_sec = (i + 1) // chunks_per_sec
                # \r をつけると、同じ行で数字だけ書き換わります
                print(f"\r >> 録音経過: {current_sec}秒 / {duration}秒 ", end="", flush=True)
        
        except Exception as e:
            print(f"録音エラー: {e}")
            break
    
    # 改行を入れておく（ログ表示が見やすくなる）
    print()

    # 無音チェック (直近3秒)
    is_finished = False
    if zeroiti is not None and len(frames) > (RATE * 3 / CHUNK):
        check_data = b''.join(frames[-int(RATE * 3 / CHUNK):])
        renzokuzero = zeroiti(check_data, RATE, 0.01, THRESHOLD)
        if 1 not in renzokuzero:
            print("無音が検知されました。")
            is_finished = True

    # 録音データを結合して文字起こし
    chunk_data = b''.join(frames)
    text = transcribe_with_cli(chunk_data)
    
    if text:
        print(f"★部分認識: {text}")

    return text, is_finished