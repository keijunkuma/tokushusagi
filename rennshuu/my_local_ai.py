# local_detector.py
import requests
import json

def detect_fraud(transcription: str) -> str:
    """
    ローカルAIサーバーと通信して詐欺判定を行う
    """
    print("--- 判定モード: ローカルAI ---")
    url = "http://localhost:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "gpt-4o",  # or your local model
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
        print(f"ローカルAIサーバーへの接続に失敗しました: {e}")
        return "エラー: 判定サーバーに接続できません"
    if __name__ == '__main__':
