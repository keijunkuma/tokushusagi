import streamlit as st
import sqlite3
import pandas as pd
import datetime

DB_PATH = "phone_blacklist.db"

# --- データベース操作関数 ---
def get_all_data():
    conn = sqlite3.connect(DB_PATH)
    # pandasを使うと表形式で一発取得できて便利です
    df = pd.read_sql_query("SELECT number, owner_name, result_text, last_updated FROM phone_history", conn)
    conn.close()
    return df

def register_data(number, name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 既存なら上書き、新規なら追加
    cur.execute('''
        INSERT INTO phone_history (number, result_text, is_dangerous, owner_name, last_updated)
        VALUES (?, ?, 0, ?, ?)
        ON CONFLICT(number) DO UPDATE SET owner_name = ?, is_dangerous = 0, last_updated = ?
    ''', (number, "家族登録済み", name, now, name, now))
    
    conn.commit()
    conn.close()

def delete_data(number):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM phone_history WHERE number = ?", (number,))
    conn.commit()
    conn.close()

# --- 画面デザイン (UI) ---
st.title("📞 防犯システム 電話帳管理")

# 1. 新規登録フォーム
with st.expander("➕ 新しい番号を登録する", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        new_number = st.text_input("電話番号", placeholder="09012345678")
    with col2:
        new_name = st.text_input("名前", placeholder="お母さん")
    
    if st.button("登録 / 更新"):
        if new_number and new_name:
            register_data(new_number, new_name)
            st.success(f"「{new_name} ({new_number})」を登録しました！")
            st.rerun() # 画面リロード
        else:
            st.error("番号と名前の両方を入力してください。")

# 2. 登録済みリスト表示
st.subheader("📋 登録リスト一覧")

df = get_all_data()

# データがある場合のみ表示
if not df.empty:
    # 検索機能
    search_query = st.text_input("🔍 リスト内を検索", "")
    if search_query:
        df = df[df.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)]

    # 表を表示 (名前、番号、メモ、更新日)
    st.dataframe(df, use_container_width=True)

    # 削除機能
    st.write("---")
    st.write("🗑️ データの削除")
    delete_num = st.selectbox("削除する番号を選択", df['number'])
    if st.button("削除実行"):
        delete_data(delete_num)
        st.warning(f"{delete_num} を削除しました。")
        st.rerun()

else:
    st.info("まだデータがありません。")