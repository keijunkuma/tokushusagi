def has_thirty_consecutive_zeros(input_list):
    """
    リストに0が30個以上連続して含まれているか判定します。

    Args:
        input_list: 判定するリスト。

    Returns:
        0が30個以上連続して存在する場合はTrue、そうでない場合はFalse。
    """
    count = 0
    for item in input_list:
        if item == 0:
            count += 1
            if count >= 30:
                return True
        else:
            count = 0
    return False

# --- テストケース ---
# 0が30個連続している場合の例
list1 = [1] * 50 + [0] * 30 + [1] * 20
print(f"リスト1の長さ: {len(list1)}")
print(f"0が30個以上連続していますか？ {has_thirty_consecutive_zeros(list1)}")

# 0が30個連続していない場合の例（途中で1が入る）
list2 = [0] * 29 + [1] + [0] * 20
print(f"リスト2の長さ: {len(list2)}")
print(f"0が30個以上連続していますか？ {has_thirty_consecutive_zeros(list2)}")

# 0が全くない場合の例
list3 = [1, 2, 3, 4, 5]
print(f"リスト3の長さ: {len(list3)}")
print(f"0が30個以上連続していますか？ {has_thirty_consecutive_zeros(list3)}")

# 0が30個以上連続している別の例
list4 = [0] * 45
print(f"リスト4の長さ: {len(list4)}")
print(f"0が30個以上連続していますか？ {has_thirty_consecutive_zeros(list4)}")