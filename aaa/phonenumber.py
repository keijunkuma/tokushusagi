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

def number_display(decoded_bits)
    index = 0
    phonedata = []
    while True:
      while len(decoded_bits) > index and decoded_bits[index] ==1 :
        index = index + 1

      if len(decoded_bits) < index + 10
        break

      block = decoded_bits[index:index+10]
      index = index + 10

      if block[0] == 1:
        print("er1")
        break

      if block[9] ==0:
        print("er2")
        break

      if sum(block[1:9]) % 2 != 0:
         print("er3")
         break

      by = block[1] + block[2] * 2 + block[3] * 4 + block[4] * 8 + block[5] * 16 + block[6] * 32 + block[7] * 64
      phonedata.append(by)

  return phonedata

def print_bytes(decoded_bytes):
    for d in decoded_bytes:
      print(format(d, '02X'),format(d, '07b'))

def number_display(decoded_bytes):
    if len(decoded_bytes) < 8:
      print("er4")
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

if __name__ == "__main__":
    _, signal = read("/content/2025_7_29 21_22_.wav")
    signal = signal / 32768.0  # Normalize
    decoded_data = decode_fsk(signal[8:], 1200, 2100, 1300, 48000)
    print(decoded_data)
    decoded_bytes = decode_bytes(decoded_data)
    print_bytes(decoded_bytes)
    number_display(decoded_bytes)

    _, signal = read("/content/2025_7_29 21_22_.wav")
    signal = signal / 32768.0  # Normalize
    decoded_data = decode_fsk(signal[6:], 1200, 2100, 1300, 48000)
    print(decoded_data)
    decoded_bytes = decode_bytes(decoded_data)
    print_bytes(decoded_bytes)
    number_display(decoded_bytes)