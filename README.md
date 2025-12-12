# tokushusagi

## 動作確認環境

Ubuntu 24.04.1 LTS

## 環境構築

```
sudo apt install python3-pip python3-venv portaudio19-dev git

git clone https://github.com/keijunkuma/tokushusagi.git

cd tokushusagi

python3 -m venv .venv
source .venv/bin/activate

pip install -U "huggingface_hub[cli]" "llama-cpp-python[server]" faster-whisper pyaudio pydantic_settings starlette_context sse_starlette fastapi starlette uvicorn llama-cpp-python[cuda]

huggingface-cli login
huggingface-cli download --local-dir medium Systran/faster-whisper-medium model.bin config.json tokenizer.json vocabulary.txt

hf download \--local-dir ./Gemma-3-4B-IT \h2oai/faster-whisper-large-v3-turbo \model.bin config.json tokenizer.json vocabulary.json



huggingface-cli download --local-dir Phi-3.1-mini-128k-instruct lmstudio-community/Phi-3.1-mini-128k-instruct-GGUF Phi-3.1-mini-128k-instruct-Q4_K_M.gguf
huggingface-cli download tensorblock/gemma-3-4b-it-GGUF   --include "gemma-3-4b-it-Q4_K_M.gguf"   --local-dir Gemma-3-4B-IT

```

## 実行

```
export SMTP_SERVER=
export FROM_EMAIL=
export TO_EMAIL=
export SMTP_PASS=

python3 -m llama_cpp.server --model ./Phi-3.1-mini-128k-instruct/Phi-3.1-mini-128k-instruct-Q4_K_M.gguf --host 0.0.0.0 --port 8080 &

python3 -m llama_cpp.server \
  --model ./Gemma-3-4B-IT/gemma-3-4b-it-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --n_gpu_layers -1
  
python3 tokushusagi.py
```
- 以下の情報を入力してください。
    - SMTP_SERVERにSMTPサーバーのアドレス
    - FROM_EMAILに送り元のアカウントのアドレス
    - TO_EMAILに送る先のアカウントのアドレス
    - SMTP_PASSにメールアカウントのパスワード

## 注意点

- 音声入力デバイスの選択
  input_device_indexの値を変更することで選択可能
arecord -D "hw:CARD=Device,DEV=0" -f S16_LE a.mp4