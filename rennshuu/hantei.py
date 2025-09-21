def zeroiti(data,rate,interval_seconds,threshold):
    # 結果を格納するリスト
    result_list = []
    # バイナリデータをnumpy配列に変換
    audio_data = np.frombuffer(data, dtype=np.int16)

    # 0.01秒間隔のデータ数
    frames_per_interval = int(rate * interval_seconds)

    # --- データ処理 ---
    for i in range(0, len(audio_data), frames_per_interval):
        end_index = i + frames_per_interval
        if end_index > len(audio_data):
            end_index = len(audio_data)
            if  end_index - i < frames_per_interval // 2:
                break
        
        chunk = audio_data[i:end_index]
        max_value = np.max(chunk)
        normalized_max_value = max_value / (2**15)
            
      
         # リストに分析結果を追加
        if normalized_max_value >= threshold:
            result_list.append(1)
        else:
            result_list.append(0)

    return result_list

if __name__ == "__main__":
    import numpy as np

    # テストケース1: しきい値を超えるデータが含まれる場合
    rate = 48000  # サンプリングレート
    interval_seconds = 0.01  # 0.01秒間隔
    threshold = 0.1  # 正規化された振幅のしきい値

    # 0.01秒ごとに0.05, 0.2, 0.05, 0.15の最大値を持つデータを生成
    test_data = np.array([int(0.05 * 32768)] * int(rate * interval_seconds) +
                         [int(0.2 * 32768)] * int(rate * interval_seconds) +
                         [int(0.05 * 32768)] * int(rate * interval_seconds) +
                         [int(0.15 * 32768)] * int(rate * interval_seconds), dtype=np.int16)
    
    result = zeroiti(test_data.tobytes(), rate, interval_seconds, threshold)
    print(f"テストケース1の結果 (期待値: [0, 1, 0, 1]): {result}")

    # テストケース2: 全てのデータがしきい値以下の場合
    test_data2 = np.array([int(0.05 * 32768)] * int(rate * interval_seconds) * 4, dtype=np.int16)
    result2 = zeroiti(test_data2.tobytes(), rate, interval_seconds, threshold)
    print(f"テストケース2の結果 (期待値: [0, 0, 0, 0]): {result2}")

    # テストケース3: 全てのデータがしきい値以上の場合
    test_data3 = np.array([int(0.2 * 32768)] * int(rate * interval_seconds) * 4, dtype=np.int16)
    result3 = zeroiti(test_data3.tobytes(), rate, interval_seconds, threshold)
    print(f"テストケース3の結果 (期待値: [1, 1, 1, 1]): {result3}")

    # テストケース4: データが1余る場合
    test_data4 = np.array([int(0.8 * 32768)]*21, dtype=np.int16)
    result4 = zeroiti(test_data4.tobytes(), 2000, 0.01, threshold)
    print(f"テストケース4の結果 (期待値: [1]): {result4}")
    # テストケース5: データがinterval_secondsの半分以上ある場合
    test_data5 = np.array([int(0.8 * 32768)]*71 , dtype=np.int16)
    result5 = zeroiti(test_data5.tobytes(), 2000, 0.01, threshold)
    print(f"テストケース5の結果 (期待値: [1, 1, 1, 1]): {result5}")
     # テストケース6: データがinterval_secondsの半分以上ない場合
    test_data6 = np.array([int(0.8 * 32768)]*61 , dtype=np.int16)
    result6 = zeroiti(test_data6.tobytes(), 2000, 0.01, threshold)
    print(f"テストケース6の結果 (期待値: [1, 1, 1]): {result6}")