import sys
import json
import os
import requests
from llama_cpp import Llama  # pip install llama-cpp-python

# --- 設定 ---
# ダウンロードしたモデルファイルのパスを正確に指定してください
MODEL_PATH = "./home/name/tokushusagi/qwen/qwen2.5-7b-instruct-q4_k_m.gguf"

# --- グローバル変数でモデルを読み込む（これ重要） ---
# 関数の中で読み込むと毎回時間がかかるため、起動時に1回だけ読み込みます
llm = None

def load_local_model():
    """ローカルモデルをメモリにロードする"""
    global llm
    if llm is None:
        if os.path.exists(MODEL_PATH):
            print(f"[{os.path.basename(__file__)}] ローカルLLMをロード中... (数秒かかります)")
            try:
                llm = Llama(
                    model_path=MODEL_PATH,
                    n_ctx=16384,      # 会話の記憶量
                    n_gpu_layers= 1,  # GPUがない場合は0
                    verbose=False    # 余計なログを消す
                )
                print("[{os.path.basename(__file__)}] ロード完了")
            except Exception as e:
                print(f"モデルのロードに失敗しました: {e}")
        else:
            print(f"警告: モデルファイルが見つかりません: {MODEL_PATH}")

# モジュールがインポートされた時点でロードを試みる
# (main.pyから import された瞬間にロードが始まります)
load_local_model()


def detect_fraud(transcription: str, provider: str = 'local') -> str:
    """
    文字起こしテキストを受け取り、詐欺かどうかを判定する
    """
    print(f"--- 判定モード: {provider} ---")

    # システムプロンプト（AIへの指示）
    # JSON形式での出力を強制する指示を追加しています
    system_prompt = """あなたは特殊詐欺防止アドバイザーです。以下の「会話テキスト」を分析し、詐欺の可能性があるかを判定してください。

【詐欺の定義】
- 親族（息子、孫）を名乗り、トラブル解決金や借金の返済を要求する（オレオレ詐欺）。
- 市役所や税務署を名乗り、還付金があると言ってATMへ誘導する（還付金詐欺）。
- 有料サイトの未納料金がある、裁判になると脅して支払わせる（架空請求）。
- 警察や銀行を名乗り、口座が犯罪に使われたと言ってカードを騙し取る。
- ウイルス感染の警告を出し、サポート費用を要求する。

【出力形式】
必ず以下の形式で出力してください。余計な挨拶やMarkdownは不要です。
{
    "fraud_probability:0から100の整数,reason: 判定理由を簡潔に（30文字以内）,alert_level: "safe" または "warning" または "danger"
}
"""

    # --- ローカル (サーバー不要版) ---
    if provider == 'local':
        if llm is None:
            return '{"error": "ローカルモデルがロードされていません"}'

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcription}
        ]

        try:
            # ここでPython内部で直接AIを動かす
            output = llm.create_chat_completion(
                messages=messages,
                temperature=0.1,  # ランダム性を低くして安定させる
                max_tokens=200,   # 長すぎる回答を防ぐ
                response_format={"type": "json_object"}  # JSON出力を強制
            )
            result = output['choices'][0]['message']['content']
            print(f"LLM回答: {result}")
            return result

        except Exception as e:
            print(f"ローカル推論エラー: {e}")
            return '{"error": "推論中にエラーが発生しました"}'

    # --- OpenAI (バックアップ用) ---
    elif provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return '{"error": "APIキーが設定されていません"}'
        
        url = "https://api.openai.com/v1/chat/completions" # URLを修正
        # ※Google経由(Gemini)を使う場合は元のURLに戻してください
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "gpt-4o-mini", # または gemini-2.5-flash
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            j = response.json()
            result = j['choices'][0]['message']['content']
            print(result)
            return result
        except Exception as e:
            print(f"API接続エラー: {e}")
            return '{"error": "API接続失敗"}'
    
    else:
        return f'{{"error": "不明なプロバイダー: {provider}"}}'

# 単体テスト用
if __name__ == "__main__":
    # テスト用テキスト
    test_text = "もしもし、市役所の保険課ですが、医療費の還付金があります。今日中にATMで手続きが必要です。"
    
    # 実行
    res = detect_fraud(test_text, "local")
    
    # 結果の確認
    print("\n--- 最終結果解析 ---")
    try:
        data = json.loads(res)
        print(f"危険度: {data.get('fraud_probability')}%")
        print(f"判定: {data.get('alert_level')}")
        print(f"理由: {data.get('reason')}")
    except:
        print("JSONとして解析できませんでした")