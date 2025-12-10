import torch
import whisper

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available (Is GPU visible?): {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
    # テスト的にモデルをGPUにロードしてみる
    try:
        model = whisper.load_model("tiny", device="cuda")
        print("Success! Whisper loaded on GPU.")
    except Exception as e:
        print(f"Error loading Whisper on GPU: {e}")
else:
    print("GPU is NOT available. Using CPU.")