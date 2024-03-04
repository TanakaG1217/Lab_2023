import time
from elasticsearch import Elasticsearch
import os
import json
from pathlib import Path
import configparser
import paho.mqtt.subscribe as subscribe
import paho.mqtt.client as mqtt
from lib import lib_TTN_mqtt5 as lib_TTN_mqtt  # 自作

# アラームを送る際の船間の距離/m
alerm_distance = 200
# 予測を行う未来時間　/s
predicted_seconds = 60


# 設定ファイル読み込み
config_path = Path(__file__).parent  # プログラムがあるディレクトリ
config_path /= "../"  # ディレクトリ移動
config_path = config_path.resolve()
config_path = os.path.join(str(config_path), "config.ini")
config_ini = configparser.ConfigParser()
config_ini.read(config_path, encoding="utf-8")


# MQTT関連
data_path_ = "..\\..\\..\\測定データ"
host = config_ini["TTN"]["host"]
port = int(config_ini["TTN"]["port"])
topic = config_ini["TTN"]["topic"]
topic_down = config_ini["TTN"]["topic_down"]
auth = {
    "username": config_ini["TTN"]["username"],
    "password": config_ini["TTN"]["password"],
}
credentials = config_ini["TTN"]["credentials"]
key = config_ini["TTN"]["key"]
connectUrl = config_ini["TTN"]["connectUrl"]
client_id = config_ini["TTN"]["client_id"]
client = mqtt.Client(client_id=client_id)  # client設定
client.username_pw_set(credentials, key)  # 名前とキーを設定
datas = {}  # ES用data格納先

# 設定ファイル読み込み
config_path = Path(__file__).parent  # プログラムがあるディレクトリ
config_path /= "../"  # ディレクトリ移動
config_path = config_path.resolve()
config_path = os.path.join(str(config_path), "config.ini")
config_ini = configparser.ConfigParser()
config_ini.read(config_path, encoding="utf-8")
# 固定データ挿入
for d in range(len(config_ini.items("data"))):
    datas[config_ini.items("data")[d][0]] = config_ini.items("data")[d][1]


# 本文で使う変数
count = 0  # 送信メッセージの文字列
# 重複回避用 デバイス毎にULメッセージの時間を辞書で管理
CurrentUL = {}


# client設定
client = mqtt.Client(client_id=client_id)
# TTNへ送信する為名前とキーを設定
client.username_pw_set(credentials, key)


# Elasticsearchへのデータ投入関数
def ES_SENT(datas):
    try:
        for i in range(len(eval(config_ini["Elasticsearch"]["host"]))):
            # Elasticsearch接続設定
            es = "http://" + eval(config_ini["Elasticsearch"]["host"])[i] + ":" + config_ini["Elasticsearch"]["port"]
            es = Elasticsearch(
                es, basic_auth=(config_ini["Elasticsearch"]["user"], config_ini["Elasticsearch"]["pass"])
            )
            try:
                es.index(index=config_ini["Elasticsearch"]["index"], document=datas)
            except Exception as error_code:  # 送信できなかった時
                error_code_ = error_code
            else:  # tryが成功したらbreakでforを抜ける
                error_code_ = None
                print("ES 投入完了")
                break
    except Exception as error_code:
        error_code_ = error_code
        print("ES 投入失敗：", error_code_)
    return None, error_code_


"""
#未実装
# CSV一斉送信プログラム
def ES_SENT_CSV():
"""

"""
#TODO TTNへ一斉パブリッシュ
送信メッセージのフォーマット
"""


# サブスクライブしたとき呼ばれるcallback関数
def TTN_onSub(tst, tst2, sub_message):
    global CurrentUL
    global datas
    RECV_DATA = {}

    # 受信データをフォーマット
    print("\n ----", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "----")
    print("ULデータを受信")
    RECV_DATA = lib_TTN_mqtt.DATA_FORMATER(sub_message)  # 想定トピックと違う場合Noneを返す
    if RECV_DATA == None:
        return
    print("ULデータ:\n ", RECV_DATA)

    # データ重複チェック
    print(f"前回のデータと比較：\n {CurrentUL}")
    dbl, check = lib_TTN_mqtt.UpdateCurrentUL(RECV_DATA, CurrentUL)  # 同じデータの時Falseを返す
    if dbl == False:
        print("前回と同じデータ")
        return
    CurrentUL = check

    # デバイスeuiに合わせた名前を追加
    for d in range(len(config_ini.items("dev_eui"))):
        if config_ini.items("dev_eui")[d][0] == RECV_DATA["device_id"]:
            RECV_DATA["device_name"] = config_ini.items("dev_eui")[d][1]
            print(
                "\n受信dev_euiが",
                {RECV_DATA["device_id"]},
                "なのでESへの保存データに",
                config_ini.items("dev_eui")[d][1],
                "を追加",
            )

    # 衝突予測
    print(f'\n{predicted_seconds}秒後に{RECV_DATA["device_name"]}と{alerm_distance}m以内のデバイスを計算')
    ALERM_dev_info = lib_TTN_mqtt.ALERM(
        RECV_DATA["device_id"], CurrentUL, alerm_distance, predicted_seconds
    )  # 衝突が予測されたデバイスの[('ID', そのデバイスの方角, そのデバイスの速度)]を返す関数
    print(f"結果：(デバイスID，そのデバイスの方角，そのデバイスの速度)\n{ALERM_dev_info[1:]}\n")

    # 衝突が予測された全デバイスへDLメッセージ送信
    if not len(ALERM_dev_info) == 1:  # 自分以外に衝突が予測されたデバイスがあるとき
        for current_tuple in ALERM_dev_info:
            other_list = [
                t for t in ALERM_dev_info if t != current_tuple
            ]  # ALERM_dev_infoからcurrent_tupleを外した配列作成
            alerm_dev_id = current_tuple[0]
            DLtopic_replace = f"v3/ryowatanabe-otaa@ttn/devices/{alerm_dev_id}/down/replace"

            SEND_DATA_pure = lib_TTN_mqtt.format_alerm_info(
                other_list, predicted_seconds
            )  # ALERMをエンドデバイスへの送信文字列に変換
            print(f" {alerm_dev_id}へDLメッセージをパブリッシュ :", SEND_DATA_pure)
            SEND_DATA = str(hex(int(SEND_DATA_pure)))[2:].zfill(11)
            # print("\n16進数変換 :", SEND_DATA)
            SEND_MESSAGE = lib_TTN_mqtt.ENCODE_BASE64(SEND_DATA)  # エンコード
            # print("base64エンコード :", SEND_MESSAGE)
            client.publish(DLtopic_replace, SEND_MESSAGE)
    else:
        print("衝突が予測されたデバイスはありませんでした．")
        SEND_DATA_pure = ""
    RECV_DATA["DLmsg"] = SEND_DATA_pure

    # ES投入
    ES_data = {**datas, **RECV_DATA}  # TODO DLmsgデータ入ってないです
    json_data = json.dumps(ES_data)
    print("\nUL/DLデータをエラスティックサーチに投入します．")
    ES_SENT(json_data)

    # データをCSV保存
    print("UL/DLデータをcsvとして保存します.")
    lib_TTN_mqtt.CREATE_CSV(RECV_DATA, data_path_)


# callback関数の設定
# パブリッシュ用
client.on_connect = lib_TTN_mqtt.on_connect2
client.on_message = lib_TTN_mqtt.on_message
client.on_publish = lib_TTN_mqtt.on_publish
# サブスクライブ用
subscribe._on_message_callback = TTN_onSub


# main
print("   ULデータがあるまで待機...\n")
client.connect(host, port, 60)
client.loop_start()
# サブスクライブしにいく
# subscribe.callback(TTN_onSub, topics=[topic], hostname=host, port=1883, auth=auth)


payload = {"downlinks": [{"f_port": 2, "frm_payload": "dGVzdDI=", "priority": "NORMAL", "confirmed": True}]}
client.publish(
    "v3/ryowatanabe-otaa@ttn/devices/eui-a84041d34184d8cf/down/replace", json.dumps(payload), qos=0, retain=False
)

while True:
    time.sleep(10)
