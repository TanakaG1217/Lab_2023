
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


def STR_BIN(data,zero):
    DATA = str( bin(data)[2:] ).zfill(zero)
    return DATA


while True:
    if gps.clean_sentences > 20: #GPSsentenceが２０文字たまったら出力する
        h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
        #出力データが整数秒
        print('日付' ,gps.date)
        print('%d 時 %d 分 %d 秒'  % (gps.timestamp[0],gps.timestamp[1],gps.timestamp[2]))

        #分
        min = int(gps.timestamp[0])*60 + int(gps.timestamp[1])
        MIN = STR_BIN(min,11)
        print('min: ',min,'    ',MIN )
        #秒
        sec = int(gps.timestamp[2])
        SEC = STR_BIN(sec,6)
        print('sec: ',sec,'   ',SEC )
        #緯度
        lati_int = int(gps.latitude[0]) - 20
        LATI_INT = STR_BIN(lati_int,5)
        lati_flt = int( float(gps.latitude[0]) %1 *100000)
        LATI_FLT = STR_BIN(lati_flt,17)
        print('緯度: ' ,lati_int ,' . ' ,lati_flt )
        print('緯度: ' ,LATI_INT ,' . ' ,LATI_FLT )
        #経度
        lon_int = int(gps.longitude[0]) - 120
        LON_INT = STR_BIN(lon_int,5)
        lon_flt = int( float(gps.longitude[0]) %1 *100000)
        LON_FLT = STR_BIN(lon_flt,17)
        print('緯度: ' ,lon_int ,' . ' ,lon_flt )
        print('緯度: ' ,LON_INT ,' . ' ,LON_FLT )
        #海抜
        alt = int(gps.altitude)
        if(alt<0):
          alt=0
        ALT = STR_BIN(alt,8)
        print('海抜: ',alt)
        #速度
        spd = int(gps.speed[2])
        SPD = STR_BIN(spd,7)
        print('速度: ', spd)
        #方向
        crs = int(gps.course)
        CRS = STR_BIN(crs,9)
        print('方向: ', crs)

        #16進数変換
        str_bin = str(MIN +SEC +LATI_INT +LATI_FLT +LON_INT +LON_FLT +ALT +SPD +CRS).zfill(88)
        #変換するために１０進数へ
        str1 = int(MIN +SEC +LATI_INT +LATI_FLT +LON_INT +LON_FLT +ALT +SPD +CRS,2)
        STR_16 = str( hex(str1)[2:] ).zfill(22)
        print('２進数データ：',str_bin)
        print('16進数データ：',STR_16)

        ser = serial.Serial('/dev/ttyUSB0',)
        ser.baudrate = 9600
        ser.bytesize = 8
        ser.parity = 'N'
        ser.stopbits = 1
        ser.timeout = 10
        ser.xonxoff = 0
        ser.rtscts = 0

        #LoRaモジュールコマンド<confirn_status>,<Fport>,<data_len>,<data>
        str2 = f'AT+SENDB=01,03,11,{STR_16}\n'
        str2=str2.encode(encoding = "UTF-8")
        print('モジュール送信データ：',str2)
        ser.write(str2)



        READ=ser.read(1000)
        print('モジュール受信データ：',READ)
        time.sleep(60.0)