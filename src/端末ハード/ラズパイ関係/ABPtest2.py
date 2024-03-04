# ABP test

import serial
import time
import threading
import micropyGPS
#import math
import re  # 文字列検索
import binascii  # ASCII
import schedule  # 定期的に実行
import os
import logging  # logファイル


# UL再送回数
max_try_count = 5


# logの出力設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
# logファイルの設定
# 現在の時刻を取得
current_time = time.localtime()
formatted_time = time.strftime("%Y-%m-%d", current_time)
log_file = os.path.abspath(__file__)  # mainファイルpath
log_file = os.path.splitext(log_file)[0]  # .py消す
# logファイル作成
current_folder = os.path.abspath(os.path.dirname(__file__))
log_folder = os.path.join(current_folder, "LoRa_log", formatted_time)
fh = logging.FileHandler(log_folder + ".log")
fh.setLevel(logging.NOTSET)
fh.setFormatter(formatter)
logger.addHandler(fh)


# gpsスレッドを作成し実行し続ける
gps = micropyGPS.MicropyGPS(9, "dd")


# (時差,緯度経度表記方法)
def rungps():  # GPSモジュールを読み、GPSオブジェクトを更新する
    s = serial.Serial("/dev/serial0", 9600, timeout=10)
    s.readline()  # 最初の1行は中途半端なデーターが読めることがあるので、捨て る
    while True:
        try:
            sentence = s.readline().decode("utf-8")  # GPSデーターを読み、文字列に変 換する
        except Exception as e:
            continue
        if sentence[0] != "$":  # 先頭が'$'でなければ捨てる
            continue
        for x in sentence:  # 読んだ文字列を解析してGPSオブジェクトにデーター を追加、更新する
            gps.update(x)


gpsthread = threading.Thread(target=rungps, args=())  # 上の関数を実行するスレッドを生成
gpsthread.daemon = True
gpsthread.start()  # スレッドを起動


# 10から2進数変換，指定したビット長へ
def STR_BIN(data, zero, low, up):
    if low <= data <= up:
        DATA = str(bin(data)[2:]).zfill(zero)
    else:
        print("データエラー：", data)
        DATA = None
    return DATA


# main
def DATA_SEND():
    if gps.clean_sentences > 20:  # GPSsentenceが２０文字たまったら出力する
        h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
        # 出力データが整数秒
        print("\n")
        print("日付", gps.date)
        print("%d 時 %d 分 %d 秒" % (gps.timestamp[0], gps.timestamp[1], gps.timestamp[2]))
        # GPSデータ整形
        # 0:00からの経過時間(分)
        min = int(gps.timestamp[0]) * 60 + int(gps.timestamp[1])
        MIN = STR_BIN(min, 11, 0, 1440)
        # 秒
        sec = int(gps.timestamp[2])
        SEC = STR_BIN(sec, 6, 0, 60)
        # 緯度
        lati_int = int(gps.latitude[0]) - 20
        LATI_INT = STR_BIN(lati_int, 5, 0, 31)
        lati_flt = int(float(gps.latitude[0]) % 1 * 100000)
        LATI_FLT = STR_BIN(lati_flt, 17, 0, 99999)
        # 経度
        lon_int = int(gps.longitude[0]) - 120
        LON_INT = STR_BIN(lon_int, 5, 0, 31)
        lon_flt = int(float(gps.longitude[0]) % 1 * 100000)
        LON_FLT = STR_BIN(lon_flt, 17, 0, 99999)
        # 海抜
        alt = int(gps.altitude)
        if alt < 0:
            alt = 0
        elif alt > 255:
            alt = 255
        ALT = STR_BIN(alt, 8, 0, 255)
        # 速度
        spd = int(gps.speed[2])
        SPD = STR_BIN(spd, 7, 0, 127)
        # 方向
        crs = int(gps.course)
        CRS = STR_BIN(crs, 9, 0, 359)

        print("0時0分からの経過分: ", min, "    ", MIN)
        print("秒: ", sec, "   ", SEC)
        print("20度からの相対緯度: ", lati_int, " . ", lati_flt)
        print("緯度: ", LATI_INT, " . ", LATI_FLT)
        print("20度からの相対緯度: ", lon_int, " . ", lon_flt)
        print("緯度: ", LON_INT, " . ", LON_FLT)
        print("海抜: ", alt)
        print("速度: ", spd)
        print("方向: ", crs)

        # Noneの場合エラーおこるので要対応
        # 済
        try:
            # 11byteの16進数へ
            str_bin = str(MIN + SEC + LATI_INT + LATI_FLT + LON_INT + LON_FLT + ALT + SPD + CRS).zfill(88)
            # 変換するために１０進数へ
            str1 = int(MIN + SEC + LATI_INT + LATI_FLT + LON_INT + LON_FLT + ALT + SPD + CRS, 2)
            STR_16 = str(hex(str1)[2:]).zfill(22)
            print("２進数データ：", str_bin)
            print("16進数データ：", STR_16)
        except Exception as e:
            print("GPSデータを16進数送信データに変換出来ませんでした．", e)
            STR_16 = ""
            return

        # LoRaモジュールコマンド<confirn_status>,<Fport>,<data_len>,<data>
        str2 = f"AT+SENDB=01,03,11,{STR_16}\n"
        print("str2:", str2)
        str2 = str2.encode(encoding="UTF-8")
        print("モジュール送信データ：", str2)
        # シリアル設定
        try:
            ser = serial.Serial(
                "/dev/ttyUSB0",
            )
            ser.baudrate = 9600
            ser.bytesize = 8
            ser.parity = "N"
            ser.stopbits = 1
            ser.timeout = 10
            ser.xonxoff = 0
            ser.rtscts = 0
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")
            return

        # 再送システム
        # 再送トライ回数
        try_count = 0

        while try_count < max_try_count:
            try_count += 1
            ser.write(str2)

            r = "read:"
            READ = ""
            #          while r != "" :
            #            r = str(ser.read())
            #            READ = READ + r

            READ = str(ser.read(250))
            print("モジュール受信データ：", READ)
            break

            """
            # シリアルで読み込んだデータに対し文字列検索
            # True or False
            TX_DONE = "txDone" in READ
            RX_DONE = "rxDone" in READ
            TIMEOUT = "rxTimeout" in READ

            if TX_DONE and RX_DONE:
                print("送信成功")
                logger.info("UL sended")
                break
            elif TX_DONE and TIMEOUT:
                print("送信タイムアウト")
                time.sleep(4.0)
            else:
                print("送信エラー")
                time.sleep(5.0)
            if try_count == 5:
                print("最大トライ回数に達しました。")
                logger.error("UL %s times failed", max_try_count)
            """

        # 受信メッセージ
        RECVB = "RECVB=?" in READ
        if RECVB:
            print("TTN受信メッセージあり")
            # コマンド送信
            str3 = "AT+RECVB=?\n"
            str3 = str3.encode(encoding="UTF-8")
            ser.write(str3)

            # 受信メッセージデコード
            READ2 = str(ser.read(30))
            #:から\までの文字を取り出す
            match = re.search(r":(.*?)(\\|$)", READ2)
            if match:
                RECV_DATA = match.group(1)
                # ASCIIデコード
                try:
                    ASCII_decoded = binascii.unhexlify(RECV_DATA).decode("utf-8")
                except Exception as e:
                    ASCII_decoded = RECV_DATA

                print("TTN受信メッセージ：", ASCII_decoded)
                logger.info("DL受信: %s", ASCII_decoded)
            else:
                print("指定のパターンが見つかりません。TTN受信データ：", READ2)
                logger.error("DL error?")


schedule.every().minutes.at(":30").do(DATA_SEND)

while True:
    schedule.run_pending()

# while True:
#    DATA_SEND()
#    time.sleep(10.0)
