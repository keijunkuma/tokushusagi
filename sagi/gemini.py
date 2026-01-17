import os
import sqlite3
import datetime
from google import genai
from google.genai import types

DB_PATH = "phone_blacklist.db"

def init_db():
    """データベースとテーブルを作成（名前カラムを追加）"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # テーブル作成: 電話番号, 判定テキスト, 危険フラグ, 名前(追加), 更新日
    cur.execute('''
        CREATE TABLE IF NOT EXISTS phone_history (
            number TEXT PRIMARY KEY,
            result_text TEXT,
            is_dangerous INTEGER,
            owner_name TEXT, 
            last_updated TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_info_from_db(bangou):
    """DBから情報（名前、危険度など）を取得する"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT owner_name, result_text, is_dangerous FROM phone_history WHERE number = ?", (bangou,))
    row = cur.fetchone()
    conn.close()
    # row = (名前, 判定テキスト, 危険フラグ)
    return row 

def register_name(bangou, name):
    """家族などの名前を登録する（安全リスト）"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 既存のデータがあれば名前だけ更新、なければ新規作成
    # 家族登録なので is_dangerous は 0 (安全) に設定
    cur.execute('''
        INSERT INTO phone_history (number, result_text, is_dangerous, owner_name, last_updated)
        VALUES (?, ?, 0, ?, ?)
        ON CONFLICT(number) DO UPDATE SET owner_name = ?, is_dangerous = 0
    ''', (bangou, "家族登録済み", name, now, name))
    
    conn.commit()
    conn.close()
    print(f"登録完了: {bangou} を「{name}」として登録しました。")

def save_scan_result(bangou, text, is_dangerous):
    """Geminiの判定結果を保存（名前がない場合はNULL）"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 名前(owner_name)は上書きしないように注意して更新
    cur.execute('''
        INSERT INTO phone_history (number, result_text, is_dangerous, last_updated)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(number) DO UPDATE SET result_text = ?, is_dangerous = ?, last_updated = ?
    ''', (bangou, text, 1 if is_dangerous else 0, now, text, 1 if is_dangerous else 0, now))
    conn.commit()
    conn.close()

def tokutei(bangou: str):
    """
    1. DBをチェック（名前があればそれを優先）
    2. なければGeminiで検索
    """
    init_db()

    if not bangou:
        return None, "番号なし", False

    # --- 1. データベース検索 ---
    db_result = get_info_from_db(bangou)
    if db_result:
        owner_name, result_text, is_dangerous = db_result
        
        # 名前が登録されているなら、それを返す
        if owner_name:
            print(f"★登録済み連絡先: {owner_name} からの着信")
            return owner_name, "登録済み", False
        
        # 名前はないけど過去に検索済み
        print(f"★DB履歴あり: {bangou}")
        return None, result_text, bool(is_dangerous)

    # --- 2. 未登録ならGeminiで検索 ---
    print(f"Gemini: {bangou} をGoogle検索中...")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None, "APIキー設定エラー", False

    try:
        client = genai.Client(api_key=api_key)
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(tools=[grounding_tool])

        prompt = (
            f"電話番号 {bangou} のGoogle検索結果に基づき、迷惑電話や詐欺の履歴があるか教えて。\n"
            f"出力の最後に、詐欺や迷惑電話の可能性が高ければ「DANGER」、安全そうなら「SAFE」、不明なら「UNKNOWN」とだけ追記して。"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=config,
        )

        full_text = response.text.strip()
        is_dangerous = False
        if "DANGER" in full_text or "詐欺" in full_text:
            is_dangerous = True
        
        # 保存
        save_scan_result(bangou, full_text, is_dangerous)
        
        return None, full_text, is_dangerous

    except Exception as e:
        print(f"Geminiエラー: {e}")
        return None, "検索エラー", False