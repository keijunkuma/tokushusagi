import numpy as np

def zeroiti(data, rate, interval_seconds, threshold):
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
            if end_index - i < frames_per_interval // 2:
                break
        
        chunk = audio_data[i:end_index]
        max_value = np.max(chunk)
        #print(f"現在のチャンクの最大値: {max_value}")
        normalized_max_value = max_value / (2**15)
        # print(normalized_max_value)    
        # int型リストに分析結果を追加
        if normalized_max_value >= threshold:
            result_list.append(1)
        else:
            result_list.append(0)

    return result_list

def interval(result_list):
    index1 = 0 
    # 閾値を超えた後にパターンをチェックする
    if 1 in result_list:
        while len(result_list) > index1:
            while len(result_list) > index1 and result_list[index1] == 0:
                index1 = index1 + 1 
            index2 = index1
            while len(result_list) > index2 and result_list[index2] == 1:
                index2 = index2 + 1
            index3 = index2
            while len(result_list) > index3 and result_list[index3] == 0:
                index3 = index3 + 1
            index4 = index3
            while len(result_list) > index4 and result_list[index4] == 1:
                index4 = index4 + 1

            if 1 <= index2 - index1 <= 5 and 45 <= index3 - index2 <= 49 and 1 <= index4 - index3 <= 5:
                return True
            
            index1 = index3
    return False