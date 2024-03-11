# ABPモードで動かすtest
import serial
import time
import threading
import micropyGPS
import re  # 文字列検索
import binascii  # ASCII
import schedule  # 定期的に実行
import os
import logging  # logファイル作成


# UL再送回数
max_try_count = 5


# logファイルの出力設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
current_time = time.localtime()
formatted_time = time.strftime("%Y-%m-%d", current_time)
log_file = os.path.abspath(__file__)  # mainファイルpath
log_file = os.path.splitext(log_file)[0]  # .py消す

current_folder = os.path.abspath(os.path.dirname(__file__))
log_folder = os.path.join(current_folder, "LoRa_log", formatted_time)
fh = logging.FileHandler(log_folder + ".log")
fh.setLevel(logging.NOTSET)
fh.setFormatter(formatter)
logger.addHandler(fh)


gps = micropyGPS.MicropyGPS(9, "dd")  # (時差,緯度経度表記方法)


# スレッドを作成し実行するための関数
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


# 10から2進数変換，指定したビット長へ
def decToBin(data, zero, low, up):
    if low <= data <= up:
        DATA = str(bin(data)[2:]).zfill(zero)
    else:
        print("データエラー：", data)
        DATA = None
    return DATA


# main
def sendGpsData():
    if gps.clean_sentences > 20:  # GPSsentenceが２０文字たまったら出力する
        h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
        # 出力データが整数秒
        print("\n")
        print("日付", gps.date)
        print("%d 時 %d 分 %d 秒" % (gps.timestamp[0], gps.timestamp[1], gps.timestamp[2]))
        # GPSデータ整形
        # 0:00からの経過時間(分)
        min = int(gps.timestamp[0]) * 60 + int(gps.timestamp[1])
        MIN = decToBin(min, 11, 0, 1440)
        # 秒
        sec = int(gps.timestamp[2])
        SEC = decToBin(sec, 6, 0, 60)
        # 緯度
        lati_int = int(gps.latitude[0]) - 20
        LATI_INT = decToBin(lati_int, 5, 0, 31)
        lati_flt = int(float(gps.latitude[0]) % 1 * 100000)
        LATI_FLT = decToBin(lati_flt, 17, 0, 99999)
        # 経度
        lon_int = int(gps.longitude[0]) - 120
        LON_INT = decToBin(lon_int, 5, 0, 31)
        lon_flt = int(float(gps.longitude[0]) % 1 * 100000)
        LON_FLT = decToBin(lon_flt, 17, 0, 99999)
        # 海抜
        alt = int(gps.altitude)
        if alt < 0:
            alt = 0
        elif alt > 255:
            alt = 255
        ALT = decToBin(alt, 8, 0, 255)
        # 速度
        spd = int(gps.speed[2])
        SPD = decToBin(spd, 7, 0, 127)
        # 方向
        crs = int(gps.course)
        CRS = decToBin(crs, 9, 0, 359)

        print("0時0分からの経過分: ", min, "    ", MIN)
        print("秒: ", sec, "   ", SEC)
        print("20度からの相対緯度: ", lati_int, " . ", lati_flt)
        print("緯度: ", LATI_INT, " . ", LATI_FLT)
        print("20度からの相対緯度: ", lon_int, " . ", lon_flt)
        print("緯度: ", LON_INT, " . ", LON_FLT)
        print("海抜: ", alt)
        print("速度: ", spd)
        print("方向: ", crs)

        # 送信するGPSデータを16進数文字列へ変換 ＊LoRaモジュールの対応が文字列のため短くする
        try:
            # 結合した文字列を2進数→10進数→16進数へ
            combined_binary_string = str(MIN + SEC + LATI_INT + LATI_FLT + LON_INT + LON_FLT + ALT + SPD + CRS).zfill(
                88
            )
            combined_dec_string = int(MIN + SEC + LATI_INT + LATI_FLT + LON_INT + LON_FLT + ALT + SPD + CRS, 2)
            combined_hex_string = str(hex(combined_dec_string)[2:]).zfill(22)
            print("２進数データ：", combined_binary_string)
            print("16進数データ：", combined_hex_string)
        except Exception as e:
            print("GPSデータを16進数送信データに変換出来ませんでした．", e)
            combined_hex_string = ""
            return

        # LoRaモジュールコマンド<confirn_status>,<Fport>,<data_len>,<data>
        str2 = f"AT+SENDB=01,03,11,{combined_hex_string}\n"
        print("str2:", str2)
        str2 = str2.encode(encoding="UTF-8")
        print("モジュール送信データ：", str2)
        # シリアル設定
        try:
            ser = serial.Serial("/dev/ttyUSB0")
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

        # 再送トライ回数
        try_count = 0

        """
        ABPモードなので再送しない
        """
        while try_count < max_try_count:
            try_count += 1
            ser.write(str2)

            readed_serial_str = ""
            # TODO シリアル通信を1文字ずつ読み込むようにする

            readed_serial_str = str(ser.read(250))
            print("モジュール受信データ：", readed_serial_str)
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
        have_RECVB = "RECVB=?" in readed_serial_str
        if have_RECVB:
            print("TTN受信メッセージあり")
            # コマンド送信
            str3 = "AT+RECVB=?\n"
            str3 = str3.encode(encoding="UTF-8")
            ser.write(str3)

            # 受信メッセージデコード
            readed_serial_str_byTTN = str(ser.read(30))
            #:から\までの文字を取り出す
            match = re.search(r":(.*?)(\\|$)", readed_serial_str_byTTN)
            if match:
                picked_str = match.group(1)
                # ASCIIデコード
                try:
                    decoed_by_ASCII = binascii.unhexlify(picked_str).decode("utf-8")
                except Exception as e:
                    decoed_by_ASCII = picked_str

                print("TTN受信メッセージ：", decoed_by_ASCII)
                logger.info("DL受信: %s", decoed_by_ASCII)
            else:
                print("指定のパターンが見つかりません。TTN受信データ：", readed_serial_str_byTTN)
                logger.error("DL error?")

if __name__ == "__main__":  
    gpsthread = threading.Thread(target=rungps, args=())  # 上の関数を実行するスレッドを生成
    gpsthread.daemon = True
    gpsthread.start()  # スレッドを起動
    schedule.every().minutes.at(":30").do(sendGpsData)

    while True:
        schedule.run_pending()

    # while True:
    #    sendGpsData()
    #    time.sleep(10.0)
