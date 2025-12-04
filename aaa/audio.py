import pyaudio
import numpy as np
import whisper  # 変更: faster_whisper から whisper に変更
from scipy.signal import resample
from zeroitihantei import zeroiti
import sys  # 変更: sysをインポート

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000  # 録音レート
SEGMENT_DURATION = 30  # 30秒ごとに文字起こし処理を実行
THRESHOLD = 0.1  # 音量の最大値の閾値

# Whisperが推奨するサンプリングレート
WHISPER_RATE = 16000

def record_and_transcribe(stream) -> str: # 変更: 'mode'引数を削除
    """
    マイクからリアルタイムで録音し、文字起こしを行う関数。
    """
    # Whisperモデルの準備
    # 変更: whisper.load_model を使用
    print("Whisperモデルをロードしています...")
    model = whisper.load_model("large-v3-turbo", device="cpu")
    print("モデルのロードが完了しました。")

    frames = []
    full_transcription = ''
    
    # 変更: リサンプルレートの計算を簡略化
    resample_factor = WHISPER_RATE / RATE

    while True:
        for _ in range(0, int(RATE * SEGMENT_DURATION / CHUNK)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        segment_data = b''.join(frames)
        # numpyバッファに変換
        buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0

        # 録音した音声を16000Hzにダウンサンプリング
        num_samples_resampled = int(buffer.shape[0] * resample_factor)
        resampled_buffer = resample(buffer, num_samples_resampled)
        
        # 変更: model.transcribe の呼び出しと結果の処理
        # fp16=False は、元のコードの compute_type="float32" に相当
        result = model.transcribe(resampled_buffer, language="ja", fp16=False)
        
        segments = result.get('segments', []) # 変更: 辞書からセグメントリストを取得

        for segment in segments:
            # 変更: 辞書のキーでアクセス
            print(f"[時間: {segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}")
        
        if len(segments) >= 2:
            for segment in segments[:-1]:
                # 変更: 辞書のキーでアクセス
                if segment['text'] not in full_transcription:
                    full_transcription += segment['text']
            
            # 最後の未処理のフレームまで戻る
            # 変更: 辞書のキーでアクセス
            last_processed_time = segments[-2]['end'] 
            
            # 変更: framesリストのインデックス計算を修正
            # (元の時間 * サンプルレート) / チャンクサイズ = framesのインデックス
            last_processed_frame_index = int(last_processed_time * RATE / CHUNK)
            
            # 録音バッファの先頭から、すでに処理した分を削除
            del frames[:last_processed_frame_index]
        
        # segment_data全体ではなく、framesリストから末尾のデータを再構築
        # (b''.joinは時間がかかるため、必要な部分だけ処理)
        check_frames = b''.join(frames[-(int(RATE * 6 / CHUNK)):])
        renzokuzero = zeroiti(check_frames, RATE, 0.01, THRESHOLD)
        
        # 0が続いたら終了
        if 1 not in renzokuzero:
            print("無音が連続しました。録音を終了します。")
            break


    # ループ終了後、残りのフレームを処理
    if frames:
        segment_data = b''.join(frames)
        buffer = np.frombuffer(segment_data, dtype=np.int16).astype(np.float32) / 32768.0

        num_samples_resampled = int(buffer.shape[0] * resample_factor)
        resampled_buffer = resample(buffer, num_samples_resampled)
        
        result = model.transcribe(resampled_buffer, language="ja", fp16=False)
        segments = result.get('segments', [])

        for segment in segments:
            print(f"[時間: {segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}")
            if segment['text'] not in full_transcription:
                full_transcription += segment['text']

    return full_transcription

if __name__ == "__main__":
    
    # scipyがインストールされているか確認
    try:
        import scipy
    except ImportError:
        print("scipyライブラリが必要です。`pip install scipy` でインストールしてください。")
        sys.exit(1)

    # 変更: 'zeroiti'のインポート確認
    try:
        import zeroitihantei
    except ImportError:
        print("警告: 'zeroitihantei' (zeroiti) モジュールが見つかりません。")
        print("無音検出機能は動作しませんが、文字起こしは続行します。")
        # 続行する

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("録音開始... (Ctrl+Cで終了)")

    # 変更: mode引数に関連する処理を削除
    # if len(sys.argv) != 2:
    #     print("使用法: python audio_handler.py <mode>")
    #     sys.exit(1)
    # mode = sys.argv[1]
    
    transcription = record_and_transcribe(stream) # 変更: 'mode'引数を削除

    stream.stop_stream()
    stream.close()
    audio.terminate()

    print("\n---最終的な文字起こし結果---")
    print(transcription)
    print("--------------------------\n")