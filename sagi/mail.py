import smtplib
import sqlite3
import os
from email.mime.text import MIMEText
from email.utils import formatdate

# データベースは電話帳と同じファイルを使います
DB_PATH = "phone_blacklist.db"

# --- データベース操作（メール用） ---
def init_email_db():
    """メールアドレス保存用のテーブルを作成"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS alert_emails (
            email TEXT PRIMARY KEY,
            owner_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_alert_email(email, name):
    """通知先メールを追加"""
    init_email_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO alert_emails VALUES (?, ?)", (email, name))
    conn.commit()
    conn.close()

def get_alert_emails():
    """登録されている全メールアドレスを取得"""
    init_email_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT email, owner_name FROM alert_emails")
    rows = cur.fetchall()
    conn.close()
    return rows # [(email, name), ...]

def delete_alert_email(email):
    """メールアドレスを削除"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM alert_emails WHERE email = ?", (email,))
    conn.commit()
    conn.close()

# --- 送信機能 ---
def send_alert_email(subject="【防犯システム】警告通知", body="詐欺の可能性があります。注意してください。"):
    """
    登録されているすべてのメールアドレスに警告を一斉送信する
    """
    # 1. 登録されたメールアドレスを取得
    recipients = get_alert_emails()
    
    if not recipients:
        print("★メール送信スキップ: 送信先が登録されていません。")
        return

    # 2. Gmail設定 (環境変数から読み込み)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    if not EMAIL_USER or not EMAIL_PASS:
        print("エラー: .env に EMAIL_USER または EMAIL_PASS が設定されていません。")
        return

    # 3. 全員に送信
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)

        for to_email, to_name in recipients:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = EMAIL_USER
            msg['To'] = to_email
            msg['Date'] = formatdate()

            server.send_message(msg)
            print(f"メール送信成功 -> {to_name} ({to_email})")

        server.quit()
        
    except Exception as e:
        print(f"メール送信エラー: {e}")

# テスト実行用
if __name__ == "__main__":
    # add_alert_email("test@example.com", "テストさん")
    send_alert_email()