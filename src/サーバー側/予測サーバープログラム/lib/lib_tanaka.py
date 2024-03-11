import datetime
import os
import csv
import json
import base64
import math
from elasticsearch import Elasticsearch


# Elasticsearchへのデータ投入関数
def sentToElastic(datas, index, config_ini):
    try:
        for i in range(len(eval(config_ini["Elasticsearch"]["host"]))):
            # Elasticsearch接続設定
            es = "http://" + eval(config_ini["Elasticsearch"]["host"])[i] + ":" + config_ini["Elasticsearch"]["port"]
            es = Elasticsearch(
                es, basic_auth=(config_ini["Elasticsearch"]["user"], config_ini["Elasticsearch"]["pass"])
            )
            try:
                es.index(index=index, document=datas)
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


# メッセージをBase64でエンコードする関数
def encodeByBase64(text):
    bytes_text = text.encode("utf-8")
    encoded = base64.b64encode(bytes_text)
    encoded_text = encoded.decode("utf-8")
    return encoded_text


def createCSV(datas, data_path):
    file_name = data_path + str(datetime.date.today()) + "_gps.csv"
    # 今日のファイルの存在確認
    if not os.path.exists(file_name):  # ファイルがない場合
        header = datas.keys()
        with open(file_name, "w", encoding="utf-8", newline="") as f:
            dictwriter = csv.DictWriter(f, fieldnames=header)
            dictwriter.writeheader()
            dictwriter.writerow(datas)
            print("CSV 書き込み完了.")
    else:
        with open(file_name, "r") as fr:  # ファイルがある場合
            reader = csv.reader(fr)
            header = next(reader)
        with open(file_name, "a", encoding="utf-8", newline="") as f:
            dictwriter = csv.DictWriter(f, fieldnames=header)
            dictwriter.writerow(datas)
            print("CSV 追加完了.\n")



"""MQTT受信のjsonから必要なもののみ抜き出す"""


def formatDATA(
    sub_data,
):
    data = {}
    try:
        m = sub_data
        msg = m.payload.decode("utf-8")
        msg = json.loads(msg)
        data["device_id"] = msg["end_device_ids"]["device_id"]
        data["hour"] = msg["uplink_message"]["decoded_payload"]["time"]["hour"]
        data["min"] = msg["uplink_message"]["decoded_payload"]["time"]["min"]
        data["sec"] = msg["uplink_message"]["decoded_payload"]["time"]["sec"]
        data["latitude"] = msg["uplink_message"]["decoded_payload"]["latitude"]
        data["longitude"] = msg["uplink_message"]["decoded_payload"]["longitude"]
        data["location"] = {}
        data["location"]["lat"] = msg["uplink_message"]["decoded_payload"]["latitude"]
        data["location"]["lon"] = msg["uplink_message"]["decoded_payload"]["longitude"]
        data["alt"] = msg["uplink_message"]["decoded_payload"]["alt"]
        data["speed"] = msg["uplink_message"]["decoded_payload"]["speed"]
        data["course"] = msg["uplink_message"]["decoded_payload"]["course"]
        rx_data = msg["uplink_message"]["rx_metadata"]
        data["RSSI"] = rx_data[0]["rssi"]
        data["SNR"] = rx_data[0]["snr"]
        data["RCVdate_UTC"] = msg["received_at"]

        return data
    except Exception as e:
        print(f">>>データフォーマットエラー<<<", e)
        return None


"""全デバイスのデータを保持するcurrentULを更新"""


# 前回のデータとデバイスID，時間を比較し同じときFalseを返す
def updateCurrentUL(data, CurrentUL):
    istrue = False
    if data["device_id"] not in CurrentUL:
        CurrentUL[data["device_id"]] = {
            "hour": data["hour"],
            "min": data["min"],
            "sec": data["sec"],
            "lat": data["latitude"],
            "lon": data["longitude"],
            "speed": data["speed"],
            "course": data["course"],
        }
        return True, CurrentUL
    else:
        for key in ["hour", "min", "sec"]:
            if data[key] != CurrentUL[data["device_id"]][key]:
                CurrentUL[data["device_id"]] = {
                    "hour": data["hour"],
                    "min": data["min"],
                    "sec": data["sec"],
                    "lat": data["latitude"],
                    "lon": data["longitude"],
                    "speed": data["speed"],
                    "course": data["course"],
                }
                istrue = True
    return istrue, CurrentUL


"""衝突予測されたデバイスのID、そのデバイスが進む方角、そのデバイスの速度を[(id,course,spd),(id,course,spd)]で返す関数たち"""


def getCollisionDevices(now_devID, CurrentUL, alerm_distance, predicted_seconds):
    alert_devices = []
    predicted_position = {}
    # 距離、方向、予測時間から　全てのデバイスの位置予測
    predicted_position = predictPosition(CurrentUL, predicted_seconds)
    # 受信したデバイスの緯度経度を取得
    now_lat = predicted_position[now_devID]["lat"]
    now_lon = predicted_position[now_devID]["lon"]
    # 他のデバイスとの距離と方角を計算し、距離がalerm_distanceｍ以内ならalert_devicesに追加
    for devID, info in predicted_position.items():
        # if devID != now_devID:
        distance = int(calculateDistance(now_lat, now_lon, info["lat"], info["lon"]))
        if distance <= alerm_distance:
            course = CurrentUL[devID]["course"]
            speed = CurrentUL[devID]["speed"]
            alert_devices.append((devID, course, speed))
    # [(devID,b,c,),(a,b,c)]のリストのタプルで返す
    return alert_devices


# CurrentULの辞書の緯度経度を、予測される緯度と経度へ更新
def predictPosition(CurrentUL, predicted_seconds):
    PREDICT_POSITION_UL = {}
    # CurrentULのID事にループ
    for device_id, data in CurrentUL.items():
        # 経過時間の計算
        data_time = datetime.datetime.now().replace(
            hour=data["hour"], minute=data["min"], second=data["sec"], microsecond=0
        )
        current_time = datetime.datetime.now()
        elapsed_time_seconds = int((current_time - data_time).total_seconds())
        # print("elapsed_time_seconds", elapsed_time_seconds)
        # 最終更新から20分経過していたらそのデバイスは位置予測しない
        if elapsed_time_seconds <= 1200:
            PREDICT_POSITION_UL[device_id] = {"lat": 0, "lon": 0}
            continue

        # 新しい位置の計算
        distance = data["speed"] * predicted_seconds / 3600
        lat = data["lat"]
        lon = data["lon"]
        bearing = data["course"]
        R = 6371.0
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        bearing_rad = math.radians(bearing)
        new_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(distance / R)
            + math.cos(lat_rad) * math.sin(distance / R) * math.cos(bearing_rad)
        )
        new_lon_rad = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(distance / R) * math.cos(lat_rad),
            math.cos(distance / R) - math.sin(lat_rad) * math.sin(new_lat_rad),
        )
        new_lat = math.degrees(new_lat_rad)
        new_lon = math.degrees(new_lon_rad)

        # 結果を辞書に追加
        PREDICT_POSITION_UL[device_id] = {"lat": new_lat, "lon": new_lon}
    return PREDICT_POSITION_UL


# 2点間の距離をメートルで計算する
def calculateDistance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    # ハバーサイン公式
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


"""衝突予測されたデバイスから送信メッセージを生成する関数"""


# リストのタプルから送信文字列へ変換
def makeAlertStr(ALERM_dev_info, predicted_seconds):
    try:
        time_str = DECtoBIN(int(predicted_seconds / 60), 4, 0, 255)
        print("\ntime:", predicted_seconds / 60, "=", time_str)
        add_str = ""
        for dev in ALERM_dev_info:
            course = DECtoBIN(int(dev[1]), 9, 0, 512)
            spd = DECtoBIN(int(dev[2]), 7, 0, 127)
            add_str += course + spd
            print("course , speed:", int(dev[1]), ",", int(dev[2]), "=", add_str)
        # print(add_str)
        add_str += time_str
        print("警告メッセージ：(...方角7ビット 速度9ビット 時間4ビット)", add_str)
    except Exception as e:
        print("format_alerm_info")
        print(e)
        return ""
    int1 = int(add_str, 2)
    SEND_DATA = str(hex(int1)[2:])
    # SEND_DATA = str(hex(str1)[2:]).zfill(22)
    return SEND_DATA


# 10から2進数変換，指定したビット長へ
def DECtoBIN(data, zero, low, up):
    if low <= data <= up:
        DATA = str(bin(data)[2:]).zfill(zero)
    else:
        # print("DECtoBIN")
        print("データエラー：", data)
        DATA = None
    return DATA


"""ESのアラーム用インデックスに投入するデータへフォーマット"""


def MakeESDataAlerm(current_tuple, CurrentUL, config_ini, utc_time):
    ES_data_alerm = {}
    ES_data_alerm["device_id"] = current_tuple[0]
    ES_data_alerm["RCVdate_UTC"] = utc_time

    # ES_data_alerm["device_name"] に 名前入れ
    dev_name = config_ini.items("dev_eui")
    for d in range(len(dev_name)):
        if dev_name[d][0] == ES_data_alerm["device_id"]:
            ES_data_alerm["device_name"] = dev_name[d][1]
            # print(ES_data_alerm["device_name"])

    # CurrentULの中の，今のデバイスのデータを入れる
    for key in CurrentUL:
        if ES_data_alerm["device_id"] == key:
            ES_data_alerm = {**ES_data_alerm, **CurrentUL[key]}
            # print(ES_data_alerm)

    # Kibanaの地図用
    ES_data_alerm["location"] = {"lat": ES_data_alerm["lat"], "lon": ES_data_alerm["lon"]}
    return ES_data_alerm
