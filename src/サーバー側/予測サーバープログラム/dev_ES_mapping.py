"""
ESに特定の型を指定してインデックスを作成する
"""

import time
from elasticsearch import Elasticsearch
import os
from pathlib import Path
import configparser

datas = {}  # ES用data格納先
mapping = {"mappings": {"properties": {"location": {"type": "geo_point"}}}}


# 設定ファイル読み込み
config_path = Path(__file__).parent  # プログラムがあるディレクトリ
config_path /= "../"  # ディレクトリ移動
config_path = config_path.resolve()
config_path = os.path.join(str(config_path), "config.ini")
config_ini = configparser.ConfigParser()
config_ini.read(config_path, encoding="utf-8")

index = config_ini["Elasticsearch"]["index2"]


# インデックスのデータ型を指定しデータ投入
def mappingToIndex(datas, index, maps):
    for i in range(len(eval(config_ini["Elasticsearch"]["host"]))):
        # Elasticsearch接続設定
        es = "http://" + eval(config_ini["Elasticsearch"]["host"])[i] + ":" + config_ini["Elasticsearch"]["port"]
        es = Elasticsearch(es, basic_auth=(config_ini["Elasticsearch"]["user"], config_ini["Elasticsearch"]["pass"]))

        try:
            # es.index(index=index, document=datas)
            es.indices.create(index=index, body=mapping)
            # es.indices.create(index=index)
        except Exception as error_code:  # 送信できなかった時
            error_code_ = error_code
        else:  # tryが成功したらbreakでforを抜ける
            error_code_ = None
            print("ES 投入完了")
            break
    print("ES 投入失敗：", error_code_)
    return



if __name__ == "__main__":
    mappingToIndex(None, index, mapping)
    time.sleep(60)
