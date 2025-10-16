from google import genai
from google.genai import types

client = genai.Client(api_key=API_KEY)

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="電話番号08057541836からかかってきた。この番号が迷惑電話や特殊詐欺をしている履歴があるか検索してほしいn\出力例迷惑電話の履歴がある電話番号です。n\出力例還付金詐欺の履歴がある電話番号です",
    config=config,
)
print(response)
print(response.text)