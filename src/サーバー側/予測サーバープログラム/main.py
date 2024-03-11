import time
import os
import json
from pathlib import Path
import configparser
import paho.mqtt.subscribe as mqtt_sub
import paho.mqtt.client
from サーバー側.予測サーバープログラム.lib import lib_tanaka as lib_tanaka  # 自作

# アラームを送る際の船間の距離/m
ALERM_DISTANCE = 50
# 予測を行う未来時間　/s
PREDEICT_SEC = 60


# 設定ファイル../config.ini読み込み
config_path = Path(__file__).parent  # プログラムがあるディレクトリ
config_path /= "../"  # ディレクトリ移動
config_path = config_path.resolve()
config_path = os.path.join(str(config_path), "config.ini")
config_ini = configparser.ConfigParser()
config_ini.read(config_path, encoding="utf-8")

# 設定ファイルからMQTT関連設定
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
mqtt_pub = paho.mqtt.client.Client(client_id=client_id)  # client設定
mqtt_pub.username_pw_set(credentials, key)  # 名前とキーを設定


# 本文で使う変数
current_UL_json = {}  # デバイス毎にULメッセージの時間を辞書で管理


"""
#TODO
ESに投入できなかった時CSVに保存しているデータを一括で投入する関数
def CSV一斉送信プログラム:
"""


# サブスクライブしたとき呼ばれるcallback関数
def on_subscribe(tst, tst2, subed_msg):
    datas_ES_sub = {}  # ES用data格納先
    datas_ES_alert = {}  # ES用data格納先（衝突予測された時に入れるインデクス）
    subed_msg = {} #受信したjsonメッセージ

    # 受信データをフォーマット
    print("\n ----", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "----")
    print("エンドデバイスからのデータを受信")
    subed_msg = lib_tanaka.formatDATA(subed_msg)  # 想定トピックと違う場合Noneを返す
    if subed_msg == None:
        return
    print("受信データ:\n ", subed_msg)

    # データ重複チェックし，重複してない時CurrentULを更新
    print(f"前回の受信データと比較：\n {current_UL_json}")
    isNew, check = lib_tanaka.updateCurrentUL(subed_msg, current_UL_json)
    if isNew == False:
        print("前回と同じデータ")
        return
    current_UL_json = check

    # サブスクライブメッセージのデバイスeuiに合わせた名前をconfig.iniから選び，subed_msgに追加
    for d in range(len(config_ini.items("dev_eui"))):
        if config_ini.items("dev_eui")[d][0] == subed_msg["device_id"]:
            subed_msg["device_name"] = config_ini.items("dev_eui")[d][1]

    # 衝突予測
    print(f"\n\n{PREDEICT_SEC}秒後に{ALERM_DISTANCE}m以内となるデバイスを計算")
    alerted_dev_tuple = lib_tanaka.getCollisionDevices(
        subed_msg["device_id"], current_UL_json, ALERM_DISTANCE, PREDEICT_SEC
    )  # 衝突が予測されたデバイスの[('ID', そのデバイスの方角, そのデバイスの速度)]を返す関数
    print(f"結果：(デバイスID，そのデバイスの方角，そのデバイスの速度)    \n{alerted_dev_tuple}\n")
    print("\n各デバイスへのメッセージ作成")

    # 衝突が予測された全デバイスへDLメッセージ送信
    if not len(alerted_dev_tuple) == 1:  # 自分以外に衝突が予測されたデバイスがあるとき
        for current_tuple in alerted_dev_tuple:
            alert_dev_info_list = [
                t for t in alerted_dev_tuple if t != current_tuple
            ]  # alerted_dev_tupleからcurrent_tupleを外した配列作成
            alerm_dev_id = current_tuple[0]
            mqtt_pub_topic = f"v3/ryowatanabe-otaa@ttn/devices/{alerm_dev_id}/down/replace"

            maked_alert_str = lib_tanaka.makeAlertStr(
                alert_dev_info_list, PREDEICT_SEC
            )  # ALERMをエンドデバイスへの送信文字列に変換
            print(f"{alerm_dev_id}へメッセージをパブリッシュ :", maked_alert_str)

            mqtt_pub_msg = lib_tanaka.encodeByBase64(maked_alert_str)  # エンコード
            mqtt_pub_info = {
                "downlinks": [{"f_port": 2, "frm_mqtt_pub_info": mqtt_pub_msg, "priority": "NORMAL", "confirmed": True}]
            }
            mqtt_pub.publish(mqtt_pub_topic, json.dumps(mqtt_pub_info))  # TTNパブリッシュ

            # デバイス毎にlora_tanaka_alermインデックスへ投入
            print("衝突が予測されたデバイスデータをESに投入")
            datas_ES_alert = lib_tanaka.MakeESDataAlerm(
                current_tuple, current_UL_json, config_ini, subed_msg["RCVdate_UTC"]
            )
            json_data = json.dumps(datas_ES_alert)
            index = config_ini["Elasticsearch"]["index2"]
            lib_tanaka.sentToElastic(json_data, index, config_ini)
    else:
        print("衝突が予測されたデバイス無し")
        maked_alert_str = ""

    subed_msg["DLmsg"] = maked_alert_str

    # ES投入
    print("\n\n受信データをエラスティックサーチに投入")
    ES_data = {**datas_ES_sub, **subed_msg}
    json_data = json.dumps(ES_data)
    index = config_ini["Elasticsearch"]["index"]
    lib_tanaka.sentToElastic(json_data, index, config_ini)

    # データをCSV保存
    print("受信データをローカルディスクにcsvとして保存")
    lib_tanaka.createCSV(subed_msg, data_path_)


def on_connect(client, userdata, flags, rc):
    print("MQTT接続に成功しました．")


def on_publish(client, userdata, mid):
    print("パブリッシュ成功しました．", client, userdata, mid)


def on_message(client, userdata, message):
    print(f"Received Message: {message.topic} {message.payload.decode()}")


if __name__ == "__main__":
    # コールバック関数を設定パブリッシュ用
    mqtt_pub.on_connect = on_connect
    mqtt_pub.on_message = on_message
    mqtt_pub.on_publish = on_publish
    # コールバック関数を設定サブスクライブ用
    mqtt_sub._on_message_callback = on_subscribe

    # publish接続
    mqtt_pub.connect(host, port, 60)
    mqtt_pub.loop_start()
    # subscribe接続
    mqtt_sub.callback(on_subscribe, topics=[topic], hostname=host, port=1883, auth=auth)
    print("   ULデータがあるまで待機...\n")
