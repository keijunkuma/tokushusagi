import torch
import whisper
import numpy as np
import sys
import os

def test_gpu_limit():
    print("="*40)
    print("🔥 Radeon Vega 8 : GPU 限界テスト 🔥")
    print("="*40)

    # 1. GPU認識チェック
    if not torch.cuda.is_available():
        print("❌ そもそもPyTorchがGPUを認識していません。")
        print("   'pip install torch ... --index-url ...rocm6.0' をやり直してください。")
        return

    gpu_name = torch.cuda.get_device_name(0)
    print(f"✅ GPU認識成功: {gpu_name}")
    print("   これから強制的にGPUロードを試みます...")

    try:
        # 2. モデルロード (tinyモデル)
        # device="cuda" で強制的にGPUメモリに乗せます
        device = "cuda"
        print(f"🔄 モデル読み込み中 (tiny / {device})...")
        
        # download_rootはカレントディレクトリにして分かりやすく
        model = whisper.load_model("tiny", device=device, download_root=".")
        print("✅ モデルロード成功！ (VRAMに乗りました)")

    except Exception as e:
        print(f"❌ モデルロード段階でクラッシュしました: {e}")
        return

    # 3. 推論テスト (ダミー音声データ)
    print("🔄 推論(文字起こし)を実行中...")
    try:
        # 30秒の無音データを作成 (サンプリングレート16000Hz)
        # Vega 8のために fp16=False (32bit計算) を指定
        dummy_audio = np.zeros(16000 * 30, dtype=np.float32)
        
        # transcribe実行
        result = model.transcribe(dummy_audio, fp16=False, language="ja")
        
        print("="*40)
        print("🎉 奇跡です！ Vega 8 で動作しました！ 🎉")
        print("結果:", result["text"])
        print("="*40)

    except RuntimeError as e:
        print("\n❌ 実行時エラー (RuntimeError):")
        print("   GPUが命令を処理できずに拒否しました。")
        print(f"   詳細: {e}")
    except Exception as e:
        print(f"\n❌ 予期せぬエラー: {e}")

if __name__ == "__main__":
    # ハングアップ対策：タイムアウトなどは設定できないため、
    # 止まったら Ctrl+C してください
    test_gpu_limit()