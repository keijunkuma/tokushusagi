# email_handler.py

# --- 標準ライブラリ ---
import os
import smtplib
from email.mime.text import MIMEText
import ssl

# 環境変数の読み込み (メール送信用)
SMTP_SERVER = os.getenv('SMTP_SERVER')
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL')
SMTP_PASS = os.getenv('SMTP_PASS')

def send_alert_email():
    """
    詐欺の可能性が高い場合に警告メールを送信する関数。
    """
    # メール情報が環境変数に設定されているか確認
    if not all([SMTP_SERVER, FROM_EMAIL, TO_EMAIL, SMTP_PASS]):
        print("警告: メールの環境変数が設定されていないため、メールは送信されません。")
        return

    # メールの内容を作成
    msg = MIMEText("詐欺の確率が高い会話が検知されました。本人に確認を取るなど、ご注意ください。", "plain", "utf-8")
    msg['Subject'] = "【重要・詐欺警告】鳥の便り リアルタイム検知サービス"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    print("警告メールを送信しています...")
    try:
        # メールサーバーに接続して送信
        context = ssl.create_default_context()
        smtpobj = smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context)
        smtpobj.login(FROM_EMAIL, SMTP_PASS)
        smtpobj.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
        smtpobj.quit()
        print("メールを送信しました。")
    except Exception as e:
        print(f"メールの送信に失敗しました: {e}")

# このファイルが直接実行された場合にのみ動くテストコード
if __name__ == "__main__":
    # このテストコードを動かすには環境変数の設定が必要です
    # 例：os.environ['SMTP_SERVER'] = 'your_server'
    send_alert_email()