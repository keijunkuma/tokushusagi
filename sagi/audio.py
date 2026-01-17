import pyaudio
import numpy as np
import subprocess
import wave
import tempfile
import os
import io          # ★追加: メモリ上でのファイル操作に必要
import requests    # ★追加: HTTP通信に必要
import sys
from scipy.signal import resample

# main.pyから呼ばれる zeroitihantei をインポート
try:
    from zeroitihantei import zeroiti
except ImportError:
    zeroiti = None


# --- 設定 ---
# サーバーのURL（自分自身のPC内）
SERVER_URL = "http://127.0.0.1:8080/inference"
# --- 設定 ---

# 録音設定
CHUNK = 1024
RATE = 48000
THRESHOLD = 0.1

def transcribe_with_server(audio_data_48k):
    """ 音声データをローカルサーバーに投げて文字起こしする (爆速版) """
    try:
        # 1. 前処理 (48kHz -> 16kHz)
        # Whisperは16kHz必須なのでリサンプリングします
        audio_np = np.frombuffer(audio_data_48k, dtype=np.int16).astype(np.float32) / 32768.0
        num_samples_target = int(len(audio_np) * 16000 / RATE)
        resampled_audio = resample(audio_np, num_samples_target)
        resampled_int16 = (resampled_audio * 32768.0).astype(np.int16)

        # 2. メモリ上でWAVファイルデータを作成 (ファイル保存しないので高速)
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(resampled_int16.tobytes())
        wav_io.seek(0) # 読み込み位置を先頭に戻す

        # 3. サーバーに送信 (POSTリクエスト)
        files = {
            'file': ('audio.wav', wav_io, 'audio/wav')
        }
        # 必要に応じてパラメータ調整 (temperatureなど)
        data = {
            'temperature': '0.0', 
            'response_format': 'json'
        }
        
        # 通信実行
        response = requests.post(SERVER_URL, files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            result_json = response.json()
            text = result_json.get('text', '').strip()
            return text
        else:
            print(f"Server Error: {response.status_code}")
            return ""

    except Exception as e:
        print(f"Whisper通信エラー(サーバーは起動していますか?): {e}")
        return ""

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
    text = transcribe_with_server(chunk_data)
    
    if text:
        print(f"★部分認識: {text}")

    return text, is_finished