from scipy.io.wavfile import read
from scipy.signal import spectrogram
import numpy as np


def decode_fsk(signal, baud_rate, f0, f1, sample_rate):
    bit_duration = sample_rate / baud_rate
    decoded_bits = []

    float_i = 0.0
    while len(signal) > float_i + bit_duration:
        segment = signal[int(float_i):int(float_i + bit_duration)]
        f, t, Sxx = spectrogram(segment, fs=sample_rate, nperseg=len(segment))

        hz1200 = Sxx[1][0]
        hz2400 = Sxx[2][0]

        if hz1200 < hz2400:
            decoded_bits.append(0)
        else:
            decoded_bits.append(1)
        float_i = float_i + bit_duration

    return decoded_bits


def decode_bytes(decoded_bits):
  index = 0
  retdata = []
  while True:
    # スタートビット0まで捨てる
    while len(decoded_bits) > index and decoded_bits[index] == 1:
      index = index + 1

    # 1つあたり10ビットなので、9ビット以下の時処理終了
    if len(decoded_bits) < index+10:
      break

    block = decoded_bits[index:index+10]
    index = index + 10

    # スタートビット0チェック
    if block[0] != 0:
      print("エラー1")
      break

    # 偶数パリティチェック
    if sum(block[1:9]) % 2 != 0:
      print("エラー2")
      break

    # ストップビット1チェック
    if block[9] != 1:
      print("エラー3")
      break

    by = block[1] + block[2] * 2 + block[3] * 4 + block[4] * 8 + block[5] * 16 + block[6] * 32 + block[7] * 64
    retdata.append(by)

  return retdata

def print_bytes(decoded_bytes):
  for d in decoded_bytes:
    print(format(d, '02X'),format(d, '07b'))

def number_display(decoded_bytes):
  if len(decoded_bytes) < 8:
    print("エラー4")
    return

  if decoded_bytes[0] == 0x10 and decoded_bytes[1] == 0x01 and decoded_bytes[2] == 0x07 and  decoded_bytes[3] == 0x10 and  decoded_bytes[4] == 0x02 and  decoded_bytes[5] == 0x40:
    print("ナンバーディスプレイ")
    bit_len = decoded_bytes[6]
    param_bits = decoded_bytes[7:7+bit_len]
    while len(param_bits) > 0:
      param_type = param_bits[0]
      param_len = param_bits[1]
      param_data = param_bits[2:2+param_len]
      param_bits = param_bits[2+param_len:]
      print(param_type, param_len, bytes(param_data).decode())
      bangou = bytes(param_data).decode()
    return bangou

if __name__ == "__main__":
    _, signal = read("/content/bbbbbbbbbb.wav")
    signal = signal / 32768.0  # Normalize
    decoded_data = decode_fsk(signal, 1200, 2100, 1300, 48000)
    print(decoded_data)
    decoded_bytes = decode_bytes(decoded_data)
    print_bytes(decoded_bytes)
    number_display(decoded_bytes)

    decoded_data = decode_fsk(signal[20:], 1200, 2100, 1300, 48000)
    print(decoded_data)
    decoded_bytes = decode_bytes(decoded_data)
    print_bytes(decoded_bytes)
    number_display(decoded_bytes)

    decoded_data = decode_fsk(signal[30:], 1200, 2100, 1300, 48000)
    print(decoded_data)
    decoded_bytes = decode_bytes(decoded_data)
    print_bytes(decoded_bytes)
    number_display(decoded_bytes)

    _, signal = read("/content/bbbbbbbbbb.wav")
    signal = signal / 32768.0  # Normalize
    decoded_data = decode_fsk(signal[10:], 1200, 2100, 1300, 48000)
    print(decoded_data)
    decoded_bytes = decode_bytes(decoded_data)
    print_bytes(decoded_bytes)
    number_display(decoded_bytes)

    decoded_data = decode_fsk(signal[20:], 1200, 2100, 1300, 48000)
    print(decoded_data)
    decoded_bytes = decode_bytes(decoded_data)
    print_bytes(decoded_bytes)
    number_display(decoded_bytes)

    decoded_data = decode_fsk(signal[30:], 1200, 2100, 1300, 48000)
    print(decoded_data)
    decoded_bytes = decode_bytes(decoded_data)
    print_bytes(decoded_bytes)
    number_display(decoded_bytes)