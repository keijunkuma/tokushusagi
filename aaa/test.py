import sys
import json
import os
from llama_cpp import Llama  # pip install llama-cpp-python

# --- 設定 ---
# ダウンロードしたモデルファイルのパスを正確に指定してください
MODEL_PATH = "/home/name/tokushusagi/Gemma-3-4B-IT/gemma-3-4b-it-Q4_K_M.gguf"

# --- グローバル変数でモデルを読み込む ---
# 起動時に1回だけ読み込み、使い回すことで高速化します
llm = None

def load_local_model():
    """ローカルモデルをメモリにロードする"""
    global llm
    if llm is None:
        if os.path.exists(MODEL_PATH):
            print(f"[{os.path.basename(__file__)}] ローカルLLMをロード中... (GPU使用設定)")
            try:
                llm = Llama(
                    model_path=MODEL_PATH,
                    n_ctx=8192,       # 会話の記憶量（必要に応じて増やす）
                    n_gpu_layers=-1,  # -1 = 全てGPUで処理（最速）
                    verbose=True     # ログを抑制
                )
                print(f"[{os.path.basename(__file__)}] ロード完了")
            except Exception as e:
                print(f"モデルのロードに失敗しました: {e}")
        else:
            print(f"警告: モデルファイルが見つかりません: {MODEL_PATH}")

# モジュールがインポートされた時点でロードを実行
load_local_model()


def detect_fraud(transcription: str, mode: str = 'default') -> str:
    """
    文字起こしテキストを受け取り、詐欺かどうかを判定する
    ※ main.py との互換性のために mode 引数を残していますが、内部では無視して常にローカルLLMを使います。
    """
    
    # モデルがロードできていない場合のガード
    if llm is None:
        return '{"fraud_probability": 0, "reason": "モデルロード失敗", "alert_level": "safe"}'

    # システムプロンプト（AIへの指示）
    system_prompt = """あなたは特殊詐欺防止アドバイザーです。以下の「会話テキスト」を分析し、詐欺の可能性があるかを判定してください。

【詐欺の定義】
- 親族（息子、孫）を名乗り、トラブル解決金や借金の返済を要求する（オレオレ詐欺）。
- 市役所や税務署を名乗り、還付金があると言ってATMへ誘導する（還付金詐欺）。
- 有料サイトの未納料金がある、裁判になると脅して支払わせる（架空請求）。
- 警察や銀行を名乗り、口座が犯罪に使われたと言ってカードを騙し取る。
- ウイルス感染の警告を出し、サポート費用を要求する。

【出力形式】
必ず以下のJSON形式のみを出力してください。挨拶やMarkdownタグは不要です。
{
    "fraud_probability": 0から100の整数,
    "reason": "判定理由を簡潔に（30文字以内）",
    "alert_level": "safe" または "warning" または "danger"
}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcription}
    ]

    try:
        # Python内部で直接AIを動かす
        output = llm.create_chat_completion(
            messages=messages,
            temperature=0.1,  # 判定を安定させるため低めに設定
            max_tokens=200,   # 長すぎる回答を防ぐ
            response_format={"type": "json_object"}  # JSON出力を強制
        )
        
        # 結果を取り出す
        result = output['choices'][0]['message']['content']
        # print(f"DEBUG(LLM回答): {result}") # デバッグしたければコメントアウトを外す
        return result

    except Exception as e:
        print(f"ローカル推論エラー: {e}")
        # エラー時もJSON形式で返すと main.py が落ちない
        return '{"fraud_probability": 0, "reason": "推論エラー", "alert_level": "safe"}'

# 単体テスト用
if __name__ == "__main__":
    # テスト用テキスト
    test_text = "もしもし、市役所の保険課ですが、医療費の還付金があります。今日中にATMで手続きが必要です。"
    
    print("--- テスト実行中 ---")
    res = detect_fraud(test_text)
    
    print("\n--- 結果 ---")
    print(res)
    
    # JSONとして読めるか確認
    try:
        data = json.loads(res)
        print(f"確率: {data.get('fraud_probability')}%")
        print(f"判定: {data.get('alert_level')}")
    except:
        print("JSON解析失敗")