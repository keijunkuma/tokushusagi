# local_detector.py
import requests
import json
import os # 問題点2を修正

# providerを引数として受け取るように修正 (問題点1)
def detect_fraud(transcription: str, provider: str) -> str:
    # 最初に変数を空にしておく
    url = ""
    model = ""
    headers = {}
    api_key = ""

    print(f"--- 判定モード: {provider} ---")

    # if文で、providerに応じた設定を割り当てる
    if provider == 'local':
        url = "http://localhost:8080/v1/chat/completions"
        model = "gpt-4o"  # ローカルで動かしているモデル名
        headers = {"Content-Type": "application/json"}

    elif provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return "エラー: 環境変数 'OPENAI_API_KEY' が設定されていません"
        
        url = "https://api.openai.com/v1/chat/completions"
        model = "gpt-4o"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    else:
        return f"エラー: '{provider}' は不明なプロバイダーです。"
    
    # --- ここからが修正部分 (問題点3, 4) ---
    # 送信するデータをここで組み立てる
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "今から文字列を送るので詐欺か詐欺ではないかだけで判断してください。出力例に完全に一致するように出してください。\n### 出力例\n詐欺の確率100%"
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # エラーがあれば例外を発生させる
        j = response.json()
        result = j['choices'][0]['message']['content']
        print(result)
        return result
    except requests.exceptions.RequestException as e:
        print(f"{provider}への接続に失敗しました: {e}")
        return f"エラー: {provider}に接続できません"