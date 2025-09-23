def itinokazu(result_list):
    index1 = 0 
# 閾値を超えた後にパターンをチェックする
    if 1 in result_list :
        while len(result_list) > index1:
            while len(result_list) > index1 and result_list[index1] ==0:
                index1 = index1 + 1 
            index2 = index1 #index1はじめの1の位置
            while len(result_list) > index2 and result_list[index2] == 1:
                index2 = index2 + 1 #index2はじめの0の位置

            if index2 - index1 >= 30 : 
                return index1
            index1 = index2
    return -1

if __name__ == "__main__":
    # テストケース1: 1が30個以上連続している場合
    itinokazu_list = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
    print(len(itinokazu_list))
    print(itinokazu(itinokazu_list))
    # テストケース2: 1が30個連続していない場合
    itinokazu_list2 = [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
    print(len(itinokazu_list2))
    print(itinokazu(itinokazu_list2))
    # テストケース3: 1の間に30個0がある場合
    itinokazu_list3 = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
    print(len(itinokazu_list3)) 
    print(itinokazu(itinokazu_list3))
    # テストケース4: 1が含まれていない場合
    itinokazu_list4 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    print(len(itinokazu_list4))
    print(itinokazu(itinokazu_list4))