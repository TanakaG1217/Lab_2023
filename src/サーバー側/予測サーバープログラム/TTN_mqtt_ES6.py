import time
import os
import json
from pathlib import Path
import configparser
import paho.mqtt.subscribe as subscribe
import paho.mqtt.client as mqtt
from lib import MyLib as MyLib  # 自作

# アラームを送る際の船間の距離/m
alerm_distance = 50
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




# 本文で使う変数
CurrentUL = {}  # デバイス毎にULメッセージの時間を辞書で管理
datas = {}  # ES用data格納先
# 固定データ挿入
for d in range(len(config_ini.items("data"))):
    datas[config_ini.items("data")[d][0]] = config_ini.items("data")[d][1]


"""
#未実装
# CSV一斉送信プログラム
def ES_SENT_CSV():
"""


# サブスクライブしたとき呼ばれるcallback関数
def TTN_onSub(tst, tst2, sub_message):
    global CurrentUL
    global datas
    RECV_DATA = {}
    ES_data_alerm = {}  # ESのアラーム用インデックスに送るよう

    # 受信データをフォーマット
    print("\n ----", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "----")
    print("エンドデバイスからのデータを受信")
    RECV_DATA = MyLib.DATA_FORMATER(sub_message)  # 想定トピックと違う場合Noneを返す
    if RECV_DATA == None:
        return
    print("受信データ:\n ", RECV_DATA)

    # データ重複チェック
    print(f"前回の受信データと比較：\n {CurrentUL}")
    dbl, check = MyLib.UpdateCurrentUL(RECV_DATA, CurrentUL)  # 同じデータの時Falseを返す
    if dbl == False:
        print("前回と同じデータ")
        return
    CurrentUL = check

    # デバイスeuiに合わせた名前を追加
    for d in range(len(config_ini.items("dev_eui"))):
        if config_ini.items("dev_eui")[d][0] == RECV_DATA["device_id"]:
            RECV_DATA["device_name"] = config_ini.items("dev_eui")[d][1]
            # print("\n受信dev_eui", {RECV_DATA["device_id"]}, "：", config_ini.items("dev_eui")[d][1])

    # 衝突予測
    print(f"\n\n{predicted_seconds}秒後に{alerm_distance}m以内となるデバイスを計算")
    ALERM_dev_info = MyLib.ALERM(
        RECV_DATA["device_id"], CurrentUL, alerm_distance, predicted_seconds
    )  # 衝突が予測されたデバイスの[('ID', そのデバイスの方角, そのデバイスの速度)]を返す関数
    print(f"結果：(デバイスID，そのデバイスの方角，そのデバイスの速度)\n      {ALERM_dev_info}\n")
    print("\n各デバイスへのメッセージ作成")

    # 衝突が予測された全デバイスへDLメッセージ送信
    if not len(ALERM_dev_info) == 1:  # 自分以外に衝突が予測されたデバイスがあるとき
        for current_tuple in ALERM_dev_info:
            other_list = [
                t for t in ALERM_dev_info if t != current_tuple
            ]  # ALERM_dev_infoからcurrent_tupleを外した配列作成
            alerm_dev_id = current_tuple[0]
            DLtopic_replace = f"v3/ryowatanabe-otaa@ttn/devices/{alerm_dev_id}/down/replace"

            SEND_DATA_pure = MyLib.format_alerm_info(
                other_list, predicted_seconds
            )  # ALERMをエンドデバイスへの送信文字列に変換
            print(f"{alerm_dev_id}へメッセージをパブリッシュ :", SEND_DATA_pure)

            SEND_MESSAGE = MyLib.ENCODE_BASE64(SEND_DATA_pure)  # エンコード
            payload = {
                "downlinks": [{"f_port": 2, "frm_payload": SEND_MESSAGE, "priority": "NORMAL", "confirmed": True}]
            }
            client.publish(DLtopic_replace, json.dumps(payload))  # TTNパブリッシュ

            # デバイス毎にlora_tanaka_alermインデックスへ投入
            print("衝突が予測されたデバイスデータをESに投入")
            ES_data_alerm = MyLib.MakeESDataAlerm(current_tuple, CurrentUL, config_ini, RECV_DATA["RCVdate_UTC"])
            json_data = json.dumps(ES_data_alerm)
            index = config_ini["Elasticsearch"]["index2"]
            MyLib.ES_SENT(json_data, index, config_ini)
    else:
        print("衝突が予測されたデバイス無し")
        SEND_DATA_pure = ""

    RECV_DATA["DLmsg"] = SEND_DATA_pure

    # ES投入
    print("\n\n受信データをエラスティックサーチに投入")
    ES_data = {**datas, **RECV_DATA}
    json_data = json.dumps(ES_data)
    index = config_ini["Elasticsearch"]["index"]
    MyLib.ES_SENT(json_data, index, config_ini)

    # データをCSV保存
    print("受信データをローカルディスクにcsvとして保存")
    MyLib.CREATE_CSV(RECV_DATA, data_path_)


if __name__ == "__main__":
    # パブリッシュ用
    client.on_connect = MyLib.on_connect2
    client.on_message = MyLib.on_message
    client.on_publish = MyLib.on_publish
    # サブスクライブ用
    subscribe._on_message_callback = TTN_onSub

    print("   ULデータがあるまで待機...\n")
    client.connect(host, port, 60)
    client.loop_start()
    # サブスクライブしにいく
    subscribe.callback(TTN_onSub, topics=[topic], hostname=host, port=1883, auth=auth)
