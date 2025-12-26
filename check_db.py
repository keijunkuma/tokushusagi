import sqlite3
import os

DB_PATH = "phone_blacklist.db"

def show_all_data():
    if not os.path.exists(DB_PATH):
        print("データベースファイルがまだありません。")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM phone_history")
        rows = cur.fetchall()
        
        print(f"--- 登録されているデータ: {len(rows)}件 ---")
        print(f"{'電話番号':<15} | {'危険度':<5} | {'更新日':<20} | 詳細")
        print("-" * 60)
        
        for row in rows:
            # row = (number, result_text, is_dangerous, last_updated)
            number = row[0]
            danger = "危険" if row[2] == 1 else "安全"
            date = row[3]
            text = row[1][:20] + "..." # 長いので最初の20文字だけ表示
            print(f"{number:<15} | {danger:<5} | {date:<20} | {text}")
            
    except sqlite3.OperationalError:
        print("テーブルがまだ作成されていません。")
    finally:
        conn.close()

if __name__ == "__main__":
    show_all_data()