import os
from gtts import gTTS
import time

def play_warning_voice(text="警告。詐欺の可能性があります。電話を切ってください。"):
    """
    指定したテキストをGoogleの音声合成で喋らせる関数
    """
    try:
        print(f"音声警告中: 「{text}」")
        
        # 1. テキストを音声(mp3)に変換
        tts = gTTS(text=text, lang='ja')
        filename = "warning_voice.mp3"
        tts.save(filename)
        
        # 2. Linuxのコマンドで再生 (mpg123を使用)
        # -q: 静かに実行(ログを出さない)
        os.system(f"mpg123 -q {filename}")
        
        # 3. 終わったらファイルを消す（残しておきたければコメントアウト）
        # os.remove(filename)
        
    except Exception as e:
        print(f"音声再生エラー: {e}")

if __name__ == "__main__":
    # テスト用
    play_warning_voice("緊急警告。この電話は詐欺の可能性があります。")