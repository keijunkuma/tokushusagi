def hantei(result_list):
  index1 = 0 
# 閾値を超えた後にパターンをチェックする
  if 1 in result_list :
    while len(result_list) > index1:
      while len(result_list) > index1 and result_list[index1] ==0:
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

      if 1 <= index2 - index1 <=5 and 45 <= index3 - index2 <= 49 and 1 <= index4 - index3 <= 5 :
        return True
      
      index1 = index3
  return False

if __name__ == "__main__":
    # テストケース2: パターンに一致しないリスト（0の数が少ない）
    # 0が44個なので、条件を満たさない
    list2 = [0] * 10 + [1] * 3 + [0] * 44 + [1] * 2 + [0] * 5
    print(f"リスト2 (期待値: False): {hantei(list2)}")
    
    # テストケース3: 1が含まれていないリスト
    list3 = [0] * 50
    print(f"リスト3 (期待値: False): {hantei(list3)}")

    # テストケース4: 2つのパターンが存在するリスト
    list4 = [0] * 10 + [1] * 3 + [0] * 47 + [1] * 2 + [0] * 5 + [1] * 2 + [0] * 48 + [1] * 3
    print(f"リスト4 (期待値: True): {hantei(list4)}")