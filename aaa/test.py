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
        model = "gemma-3-4b-it-Q4_K_M"  # ローカルで動かしているモデル名
        headers = {"Content-Type": "application/json"}

    elif provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return "エラー: 環境変数 'OPENAI_API_KEY' が設定されていません"
        
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        model = "gemini-2.5-flash"
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
                "content": "特殊詐欺とはこういった例があります。\n- 息子や孫などの親族を名乗り、トラブルの解決金などの名目で金銭を要求する手口です。\n- 有料サイトの未納料金など、身に覚えのない請求で金銭をだまし取る手口です。自動音声やSMSから誘導し、電話で「有料サイトの利用料金が未納だ。払わないと裁判になる」と電子マネー購入を要求。業者を名乗り、「あなたの個人情報が流出している。保護するために金を振り込んでほしい」と要求。\n- 市役所や税務署の職員を名乗り、医療費や税金の還付金があると偽ってATMを操作させ、お金を振り込ませる手口です。\n- 警察官や銀行協会の職員などを名乗り、「あなたの口座が犯罪に利用されている」などと嘘を言ってキャッシュカードをだまし取る手口です。\n- インターネットの閲覧中に「ウイルスに感染しました」などの偽の警告画面を表示させ、解決するために電話をかけさせて金銭をだまし取る手口です。\n- これまでのATMへ誘導する手口に加え、近年では電話で指示を出し、被害者自身のスマートフォンやパソコンでネットバンキングを操作させて送金させる手口も増えています。\n\n\n以下の会話文は電話でかかってきた会話を文字起こししたものです。\n会話の内容が上記に近いか割合を表示してください。"
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
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("使用法: python local_detector.py <transcription> <provider>")
        sys.exit(1)
        
    transcription = sys.argv[1]
    provider = sys.argv[2]
        
    result = detect_fraud(transcription, provider)
    print("\n--- 判定結果 ---")
    print(result)
    print("-----------------")
    sys.exit(0)