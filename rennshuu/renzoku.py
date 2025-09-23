def has_ten_consecutive_ones(input_list):
    """
    リストに1が10個連続して含まれているか判定します。

    Args:
        input_list: 判定するリスト。

    Returns:
        1が10個連続して存在する場合はTrue、そうでない場合はFalse。
    """
    count = 0
    for item in input_list:
        if item == 1:
            count += 1
            if count >= 30:
                return True
        else:
            count = 0
    return False

# テストケース
# 1が10個連続している場合の例
list1 = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 2]
print(f"リスト1: {list1}")
print(f"1が10個連続していますか？ {has_ten_consecutive_ones(list1)}")

# 1が10個連続していない場合の例
list2 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1]
print(f"リスト2: {list2}")
print(f"1が10個連続していますか？ {has_ten_consecutive_ones(list2)}")

# 1が10個以上連続している場合の例
list3 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
print(f"リスト3: {list3}")
print(f"1が10個連続していますか？ {has_ten_consecutive_ones(list3)}")

# そもそも1がない場合の例
list4 = [0, 2, 3, 4, 5]
print(f"リスト4: {list4}")
print(f"1が10個連続していますか？ {has_ten_consecutive_ones(list4)}")