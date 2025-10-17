import os
from google import genai
from google.genai import types

def tokutei(bangou: str):
    """
    電話番号を受け取り、Geminiを使って迷惑電話の履歴を検索し、結果を返す
    """
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("APIキーが設定されていません。.envファイルを確認してください。")

    if not bangou:
        print("Gemini: 電話番号が渡されなかったため、調査をスキップします。")
        return "調査スキップ（電話番号なし）"

    client = genai.Client(api_key=api_key)

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents="電話番号" + bangou + "からかかってきた。この番号が迷惑電話や特殊詐欺をしている履歴があるか検索してほしいn\出力例迷惑電話の履歴がある電話番号です。n\出力例還付金詐欺の履歴がある電話番号です",
        config=config,
    )

    print(response.text)
    
    return response.text.strip()

    try:
        pass
    except Exception as e:
        print(f"Gemini APIの呼び出し中にエラーが発生しました: {e}")
        return "情報の取得中にエラーが発生しました。"

if __name__ == "__main__":
    tokutei("08011111111")
