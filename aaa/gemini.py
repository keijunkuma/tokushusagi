from google import genai
from google.genai import types

# API_KEYをここに設定してください
# genai.configure(api_key="YOUR_API_KEY")

def tokutei(bangou):
    # APIキーは関数の外で一度だけ設定するのがおすすめです
    client = genai.Client() # configureを使っていればAPIキーは不要

    # Google検索を有効にするためのツールを作成
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    # f-stringを使って、変数と文字列を1つにまとめる
    prompt = f"電話番号「{bangou}」からかかってきた。この番号が迷惑電話や特殊詐欺に関わっている履歴があるか検索してほしい。\n\n出力例：迷惑電話の履歴がある電話番号です。\n出力例：還付金詐欺の履歴がある電話番号です。"

    # generate_contentを呼び出す
    response = client.generative_models.generate_content(
        model="gemini-2.5-flash-lite", # モデル名を修正（liteはつかないことが多い）
        contents=prompt,
        tools=[grounding_tool], # configではなくtools引数でツールを渡す
    )
    
    # レスポンスと、その中のテキスト部分を出力
    print(response)
    print(response.text)

# 関数を呼び出す例
# tokutei("090-XXXX-XXXX")