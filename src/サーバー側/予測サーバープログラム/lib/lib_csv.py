#他のプログラムで流用可能
import datetime
import os
import csv
import glob
import time

#CSV作成プログラム
def CREATE_CSV(datas, data_path):
    date = datetime.date.today() #CSVファイル名の日付取得
    file_name = str(data_path) + "/" + str(datas["number"]) + "_" + str(date) + ".csv"
    #file_name = data_path + "\\" + "data_" + str(date) + ".csv"

    #今日のファイルの存在確認
    if not os.path.exists(file_name): #ファイルがない場合
        header = datas.keys()
        with open(file_name, 'w',encoding='utf-8',newline='') as f:
            dictwriter = csv.DictWriter(f, fieldnames=header)
            dictwriter.writeheader()
            dictwriter.writerow(datas)
    else:
        with open(file_name, 'r') as fr: #ファイルがある場合
            reader = csv.reader(fr)
            header = next(reader)
        with open(file_name, 'a',encoding='utf-8',newline='') as f:
            dictwriter = csv.DictWriter(f, fieldnames=header)
            dictwriter.writerow(datas)

def DELIET_CSV(file_):
    os.remove(file_)
