from scipy.io.wavfile import read
from scipy.signal import spectrogram
import numpy as np


def decode_fsk(signal, baud_rate, f0, f1, sample_rate):
    """
    FSK信号をデコードし、ビット列を返す。
    Args:
        signal (np.ndarray): デコードする音声信号。
        baud_rate (int): ボーレート（1秒あたりのシンボル数）。
        f0 (int): '0'に対応する周波数。
        f1 (int): '1'に対応する周波数。
        sample_rate (int): サンプリングレート。
    Returns:
        list: デコードされたビット列。
    """
    bit_duration = int(sample_rate / baud_rate)
    decoded_bits = []

    # 周波数ビンを見つける
    f, _, _ = spectrogram(signal, fs=sample_rate)
    # f0, f1に最も近い周波数のインデックスを見つける
    idx_f0 = np.argmin(np.abs(f - f0))
    idx_f1 = np.argmin(np.abs(f - f1))
    
    # 信号の端を処理するため、ループの条件を変更
    for i in range(0, len(signal) - bit_duration, bit_duration):
        segment = signal[i:i + bit_duration]
        # スペクトログラムを計算（1セグメント全体でFFTを実行）
        # npersegをセグメントの長さに合わせることで、周波数の分解能を最大化
        _, _, Sxx = spectrogram(segment, fs=sample_rate, nperseg=len(segment), noverlap=0)
        
        # Sxxは二次元配列になるが、時間軸は1点なので[0]でアクセス
        power_f0 = Sxx[idx_f0][0]
        power_f1 = Sxx[idx_f1][0]

        if power_f0 > power_f1:
            decoded_bits.append(0)
        else:
            decoded_bits.append(1)
            
    return decoded_bits


def decode_bytes(decoded_bits):
    """
    ビット列をバイト列にデコードする。
    Args:
        decoded_bits (list): デコードされたビット列。
    Returns:
        list: デコードされたバイト列。
    """
    index = 0
    phonedata = []
    
    while True:
        # スタートビット（0）を探す
        while len(decoded_bits) > index and decoded_bits[index] == 1:
            index += 1

        # 10ビット（スタートビット1、データ8、ストップビット1）のブロックがあるか確認
        if len(decoded_bits) < index + 10:
            break

        block = decoded_bits[index:index + 10]
        index += 10

        # スタートビットが0であるかチェック
        if block[0] != 0:
            print("er1: Start bit is not 0")
            continue

        # ストップビットが1であるかチェック
        if block[9] != 1:
            print("er2: Stop bit is not 1")
            continue
        
        # パリティチェック（偶数パリティを想定）
        # スタート、ストップビットを除いた8ビットの和が偶数か
        parity_sum = sum(block[1:9])
        if parity_sum % 2 != 0:
            print("er3: Parity check failed")
            continue

        # LSB-firstでバイトを組み立て
        # block[1]がLSB、block[8]がMSB
        by = 0
        for i in range(8):
            by += block[i + 1] * (2 ** i)

        phonedata.append(by)

    return phonedata


def print_bytes(decoded_bytes):
    """
    デコードされたバイト列を16進数と2進数で表示する。
    """
    for d in decoded_bytes:
        print(f"{d:02X} {d:08b}")


def number_display(decoded_bytes):
    """
    ナンバーディスプレイ情報を解析し表示する。
    """
    if len(decoded_bytes) < 8:
        print("er4: Data length is too short")
        return

    # NTTのナンバーディスプレイフォーマットを想定
    if (decoded_bytes[0] == 0x02 and decoded_bytes[1] == 0x01 and
        decoded_bytes[2] == 0x07 and decoded_bytes[3] == 0x10 and
        decoded_bytes[4] == 0x02 and decoded_bytes[5] == 0x40):
        
        print("ナンバーディスプレイ")
        data_len = decoded_bytes[6] # 全体のデータ長
        data_bytes = decoded_bytes[7:7 + data_len]
        
        while len(data_bytes) > 0:
            param_type = data_bytes[0]
            param_len = data_bytes[1]
            param_data = data_bytes[2:2 + param_len]
            
            # 残りのデータを更新
            data_bytes = data_bytes[2 + param_len:]
            
            try:
                # バイト列を文字列にデコード
                # 日本語（シフトJIS）の場合は 'shift_jis' を使う
                decoded_str = bytes(param_data).decode('ascii')
                print(f"Type: {param_type:02X}, Length: {param_len:02X}, Data: {decoded_str}")
            except UnicodeDecodeError:
                print(f"Type: {param_type:02X}, Length: {param_len:02X}, Data: (decode error)")

if __name__ == "__main__":
    # ファイル名とパスは適宜変更してください
    try:
        sample_rate, signal = read("/content/2025_7_29 21_22_.wav")
    except FileNotFoundError:
        print("ファイルが見つかりません。パスを確認してください。")
        exit()
        
    # floatに変換し、正規化
    signal = signal.astype(np.float32) / 32768.0

    # 1回目のデコード
    # f0とf1の周波数を正しい値に修正（多くのFSKモデムは1200Hzと2200Hzを使う）
    # 元のコードの1200, 2400は誤り
    # ここでは一般的な値として1200Hzと2200Hzを使用
    print("--- 1回目のデコード ---")
    decoded_data1 = decode_fsk(signal[8:], 1200, 1200, 2200, sample_rate)
    print("デコードされたビット:", decoded_data1)
    decoded_bytes1 = decode_bytes(decoded_data1)
    print_bytes(decoded_bytes1)
    number_display(decoded_bytes1)

    print("\n" + "="*40 + "\n")

    # 2回目のデコード
    print("--- 2回目のデコード ---")
    decoded_data2 = decode_fsk(signal[6:], 1200, 1200, 2200, sample_rate)
    print("デコードされたビット:", decoded_data2)
    decoded_bytes2 = decode_bytes(decoded_data2)
    print_bytes(decoded_bytes2)
    number_display(decoded_bytes2)