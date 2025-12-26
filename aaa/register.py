from gemini import register_name

print("--- 電話帳登録ツール ---")
while True:
    number = input("\n電話番号を入力してください (終了するには q ): ")
    if number == 'q':
        break
    
    name = input(f"{number} の名前を入力してください (例: お母さん): ")
    
    register_name(number, name)