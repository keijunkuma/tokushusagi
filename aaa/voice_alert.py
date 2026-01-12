import os
import subprocess

# ★成功したデバイスアドレス
SPEAKER_ADDRESS = "plughw:1,0"

def voice_alert(text):
    """
    Open JTalkを使って、綺麗な日本語で読み上げる関数
    （音量ブースト版）
    """
    print(f"★読み上げ中: {text}")
    
    filename = "alert_temp.wav"
    dic_path = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
    voice_path = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"
    
    try:
        # ★ここを変更！ -g 20 を追加して音量を大きくしました
        # もし音が割れて聞き取りづらい場合は、20 を 10 や 15 に下げてください
        cmd = f'echo "{text}" | open_jtalk -x {dic_path} -m {voice_path} -ow {filename} -g 20'
        
        # 1. 音声ファイル作成
        os.system(cmd)
        
        # 2. 再生
        if os.path.exists(filename):
            # 音声ファイルがあるか確認してから再生
            os.system(f"aplay -D {SPEAKER_ADDRESS} -q {filename}")
            os.remove(filename)
            
    except Exception as e:
        print(f"読み上げエラー: {e}")

# テスト実行
if __name__ == "__main__":
    voice_alert("警告します。詐欺の可能性があります。注意してください")