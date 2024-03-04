import serial
import time
import threading
import micropyGPS
import math

gps = micropyGPS.MicropyGPS(9, 'dd')
# MicroGPSオブジェクトを生成する。
# 引数はタイムゾーンの時差と出力フォーマット


def rungps(): # GPSモジュールを読み、GPSオブジェクトを更新する
    s = serial.Serial('/dev/serial0', 9600, timeout=10)
    s.readline() # 最初の1行は中途半端なデーターが読めることがあるので、捨てる
    while True:
        sentence = s.readline().decode('utf-8') # GPSデーターを読み、文字列に変換する
        if sentence[0] != '$': # 先頭が'$'でなければ捨てる
            continue
        for x in sentence: # 読んだ文字列を解析してGPSオブジェクトにデーターを追加、更新する
            gps.update(x)

gpsthread = threading.Thread(target=rungps, args=()) # 上の関数を実行するスレッドを生成
gpsthread.daemon = True
gpsthread.start() # スレッドを起動


# 緯度の小数部分を16進数表現に変換する
def CONVERT_TO_HEX(CON):
     CON_math = math.modf(CON)[0]
     CON_4 = float(round(CON_math, 4))*10000
     CON_4_trunce = int(CON_4 // 100)*100
     CON_4_trunce = CON_4 - CON_4_trunce
     if CON_4_trunce < 10:
             CON_4 = hex(int(CON_4_trunce))
             CON_4 = int(CON_4[2:])
             CON_4 = format(CON_4, "0=2")
     else:
             CON_4 = hex((int(CON_4_trunce)))[2:]
     return  CON_4


while True:
    if gps.clean_sentences > 20: #ちゃんとしたデーターがある程度たまったら出力する
        h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
        print('現在時刻：%' ,gps.timestamp)
        print('緯度経度: %2.8f, %2.8f' % (gps.latitude[0], gps.longitude[0]))
        print('海抜: %f' % gps.altitude)

        Lati = str(hex(int(float(gps.latitude[0]))))[2:]
        lati_2 = int(float(gps.latitude[0]) * 100) % 100
        Lati_2 = str(hex(lati_2))[2:]
        Lati_4 = CONVERT_TO_HEX(gps.latitude[0])

        Lon = str(hex(int(float(gps.longitude[0]))))[2:]
        lon_2 = int(float(gps.longitude[0]) * 100) % 100
        Lon_2 = str(hex(int(lon_2)))[2:]
        Lon_4 = CONVERT_TO_HEX(gps.longitude[0])

        Alt = str(hex(int(float(gps.altitude))))[2:]

        #GPSの速度測定2桁０挿入
        spd = int(float(gps.speed[2]))
        SPD = str(hex(spd)[2:]).zfill(2)
        print('速度(10進数,16進数):', spd,' , ',SPD)

        #GPSの進行方向測定４桁になるよう調整
        crs = int(float(gps.course))
        CRS = str(hex(crs)[2:]).zfill(4)
        print('方向(10進数,16進数):', crs,'  , ',CRS)

        str1 = (Lati+Lati_2+Lati_4   +Lon+Lon_2+Lon_4  +SPD + CRS )
        print('TTN送信データ：', str1)

        ser = serial.Serial('/dev/ttyUSB0',)
        ser.baudrate = 9600
        ser.bytesize = 8
        ser.parity = 'N'
        ser.stopbits = 1
        ser.timeout = 10
        ser.xonxoff = 0
        ser.rtscts = 0

        #LoRaモジュールコマンド<confirn_status>,<Fport>,<data_len>,<data>
        str2 = f'AT+SENDB=01,03,9,{str1}\n'
        str2=str2.encode(encoding = "UTF-8")
        print(str2)
        ser.write(str2)
        ser.read()
        time.sleep(20.0)