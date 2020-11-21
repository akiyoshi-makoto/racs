#!/usr/bin/env python
import os
import csv

############################################################
# リスト(登録者 or 在室者)から読込
############################################################
def read_list(kind):
    if os.path.isfile(kind):
        with open(kind, 'r', encoding='utf-8') as csvfile:
            file = csv.reader(csvfile)
            list = [row for row in file]
    else:
        list = []
    return list

############################################################
# リスト(登録者 or 在室者)への書込
############################################################
def write_list(list, kind):
    with open(kind, 'w', newline='', encoding='utf-8') as csvfile:
        file = csv.writer(csvfile)
        file.writerows(list)

############################################################
# 入退室時のログ書込
############################################################
def write_log(now_time, list, index, in_out_info):
    # ログファイルはWindows PCで開くことを想定しているためS-JISでエンコードする。
    with open(now_time.strftime('%Y-%m') + '.csv', 'a', newline='', encoding='shift_jis') as csvfile:
        file = csv.writer(csvfile)
        file.writerow([list[index][0],                   # Felica ID
                        str(list[index][1]),             # 社員No
                        list[index][2],                  # 社員氏名
                        now_time.strftime('%Y-%m-%d'),   # 年月日
                        now_time.strftime('%H:%M:%S'),   # 時刻
                        in_out_info])                    # 入退室情報

############################################################
# 強制退室処理時のログ書込
############################################################
def write_log_force_exit(now_time, list):
    # ログファイルはWindows PCで開くことを想定しているためS-JISでエンコードする。
    with open(now_time.strftime('%Y-%m') + '.csv', 'a', newline='', encoding='shift_jis') as csvfile:
        file = csv.writer(csvfile)

        for index in range(len(list)):
            file.writerow([list[index][0],                   # Felica ID
                            str(list[index][1]),             # 社員No
                            list[index][2],                  # 社員氏名
                            now_time.strftime('%Y-%m-%d'),   # 年月日
                            now_time.strftime('%H:%M:%S'),   # 時刻
                            'FORCE_EXIT'])                   # 入退室情報
