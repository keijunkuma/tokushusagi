# cloud_detector.py
import requests
import json
import os

# クラウドサービスのAPIキーを環境変数から読み込む
API_KEY = os.getenv('CLOUD_API_KEY')
# クラウドサービスのAPIエンドポイント（これは仮のURLです）
API_URL = "https://api.gemini.google.com/v1/models/gemini-pro:generateContent" # 例：Gemini API

def detect_fraud(transcription: str) -> str:
    """
    クラウドAIサービスと通信して詐欺判定を行う
    """
    print("--- 判定モード: クラウドAI ---")
    if not API_KEY:
        return "エラー: 環境変数 'CLOUD_API_KEY' が設定されていません"

    headers = {
        'Content-Type': 'application/json',
    }
    # APIの仕様に合わせてデータを構築
    data = {
        "contents": [{
            "parts":[{
                "text": f"今から文字列を送るので詐欺か詐欺ではないかだけで判断してください。出力例に完全に一致するように出してください。\n### 出力例\n詐欺の確率100%\n\n---\n\n{transcription}"
            }]
        }]
    }
    
    try:
        response = requests.post(f"{API_URL}?key={API_KEY}", headers=headers, data=json.dumps(data))
        response.raise_for_status()
        j = response.json()
        result = j['candidates'][0]['content']['parts'][0]['text']
        print(result)
        return result
    except requests.exceptions.RequestException as e:
        print(f"クラウドAIへの接続に失敗しました: {e}")
        return "エラー: クラウドサービスに接続できません"