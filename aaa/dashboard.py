import streamlit as st
import sqlite3
import pandas as pd
import datetime

# mail.py からDB操作関数を読み込む
# ※もしエラーが出る場合は、mail.pyの関数をここにコピペしてもOKです
try:
    from mail import add_alert_email, delete_alert_email, get_alert_emails
except ImportError:
    st.error("mail.py が見つかりません。同じフォルダに置いてください。")

DB_PATH = "phone_blacklist.db"

def init_db():
    """ データベースとテーブルが存在しない場合に作成する """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # テーブル作成（すでにあったら何もしない）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS phone_history (
            number TEXT PRIMARY KEY,
            owner_name TEXT,
            result_text TEXT,
            is_dangerous INTEGER,
            last_updated TEXT
        )
    """)
    conn.commit()
    conn.close()

# アプリ起動時に必ず実行して、テーブルを作る
init_db()

# --- 電話帳用DB関数 ---
# --- 電話帳用DB関数 (修正版) ---
def get_phone_data():
    conn = None
    df = pd.DataFrame()
    try:
        # timeout=10.0 でロック待ち時間を確保
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        df = pd.read_sql_query("SELECT number, owner_name, result_text, last_updated FROM phone_history", conn)
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
    finally:
        if conn:
            conn.close()
    return df

def register_phone(number, name):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cur = conn.cursor()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 全角スペースを削除し、綺麗なSQLにしました
        sql = """
            INSERT INTO phone_history (number, result_text, is_dangerous, owner_name, last_updated)
            VALUES (?, ?, 0, ?, ?)
            ON CONFLICT(number) DO UPDATE SET owner_name = ?, is_dangerous = 0, last_updated = ?
        """
        
        cur.execute(sql, (number, "家族登録済み", name, now, name, now))
        conn.commit()
    except Exception as e:
        st.error(f"登録エラー: {e}")
        raise e # エラーを呼び出し元に伝えて停止させる
    finally:
        if conn:
            conn.close()

def delete_phone(number):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cur = conn.cursor()
        cur.execute("DELETE FROM phone_history WHERE number = ?", (number,))
        conn.commit()
    except Exception as e:
        st.error(f"削除エラー: {e}")
    finally:
        if conn:
            conn.close()

# ==========================================
#  画面レイアウト
# ==========================================
st.set_page_config(page_title="防犯システム管理", layout="centered")
st.title("🛡️ 防犯システム 管理画面")

# タブを作成
tab1, tab2 = st.tabs(["📞 電話帳設定", "📧 通知メール設定"])

# --- タブ1: 電話番号管理 ---
with tab1:
    st.header("着信時の名前表示")
    st.caption("ここで登録した番号から電話が来ると、AIが名前を読み上げます。")

    # 新規登録
    with st.expander("➕ 電話番号を追加", expanded=True):
        col1, col2 = st.columns(2)
        p_num = col1.text_input("電話番号", placeholder="09012345678", key="p_num")
        p_name = col2.text_input("名前", placeholder="お母さん", key="p_name")
        
        if st.button("電話帳に登録", key="btn_phone"):
            if p_num and p_name:
                register_phone(p_num, p_name)
                st.success(f"登録しました: {p_name}")
                st.rerun()
            else:
                st.warning("番号と名前を入力してください")

    # 一覧表示
    df_phone = get_phone_data()
    if not df_phone.empty:
        st.dataframe(df_phone, use_container_width=True)
        
        # 削除
        del_target = st.selectbox("削除する番号", df_phone['number'], key="sel_del_phone")
        if st.button("番号を削除", key="btn_del_phone"):
            delete_phone(del_target)
            st.warning("削除しました")
            st.rerun()
    else:
        st.info("登録データがありません")

# --- タブ2: 通知メール管理 ---
with tab2:
    st.header("警告メールの送信先")
    st.caption("詐欺と判定された時、ここに登録された全員へメールを送ります。")

    # 新規登録
    with st.expander("➕ 送信先メールを追加", expanded=True):
        col1, col2 = st.columns(2)
        m_addr = col1.text_input("メールアドレス", placeholder="taro@example.com", key="m_addr")
        m_name = col2.text_input("所有者名", placeholder="自分 / 息子", key="m_name")
        
        if st.button("メールアドレス登録", key="btn_mail"):
            if m_addr and m_name:
                add_alert_email(m_addr, m_name)
                st.success(f"追加しました: {m_name}")
                st.rerun()
            else:
                st.warning("アドレスと名前を入力してください")

    # 一覧表示
    # mail.pyの関数を使ってリスト取得
    try:
        rows = get_alert_emails() # [(email, name), ...]
        if rows:
            # 見やすくデータフレームに変換
            df_mail = pd.DataFrame(rows, columns=["メールアドレス", "名前"])
            st.table(df_mail)
            
            # 削除
            del_mail_target = st.selectbox("削除するアドレス", df_mail['メールアドレス'], key="sel_del_mail")
            if st.button("アドレスを削除", key="btn_del_mail"):
                delete_alert_email(del_mail_target)
                st.warning("削除しました")
                st.rerun()
        else:
            st.info("登録されているメールアドレスはありません。")
            
    except Exception as e:
        st.error(f"データ取得エラー: {e}")