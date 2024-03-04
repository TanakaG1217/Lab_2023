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
     return  CON


while True:
    if gps.clean_sentences > 20: #GPSsentenceが２０文字たまったら出力する
        h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
        #出力データが整数秒
        print('%d 時 %d 分 %d 秒'  % (gps.timestamp[0],gps.timestamp[1],gps.timestamp[2]))
        print('緯度経度: %2.6f, %2.6f' % (gps.latitude[0], gps.longitude[0]))
        print('海抜: %.1f' % gps.altitude) #出力データが小数点以下１桁まで

        #緯度経度8桁
        lati_int = int(gps.latitude[0])
        lati_flt = int( float(gps.latitude[0]) %1 *100000 )
        LATI = ( str( hex(lati_int)[2:] ).zfill(3) + str( hex(lati_flt)[2:] ).zfill(5) )
        print('緯度 ' ,lati_int ,' . ' ,lati_flt )

        lon_int = int(gps.longitude[0])
        lon_flt = int( float(gps.longitude[0]) %1 *100000 )
        LON = ( str( hex(lon_int)[2:] ).zfill(3) + str( hex(lon_flt)[2:] ).zfill(5) )
        print('経度 ' ,lon_int ,' . ' ,lon_flt )

 #       lon = int( float(gps.longitude[0])*100000 )
#        Lon = str( hex(lon)[2:] ).zfill(7)

        #海抜3桁
        alt = int( float(gps.altitude) )
        ALT = str( hex(alt)[2:] ).zfill(3)

        #速度2桁
        spd = int(float(gps.speed[2]))
        SPD = str(hex(spd)[2:]).zfill(2)
        print('速度(10進数,16進数):', spd,' , ',SPD)

        #方向3桁
        crs = int(float(gps.course))
        CRS = str(hex(crs)[2:]).zfill(3)
        print('方向(10進数,16進数):', crs,'  , ',CRS)

        #時刻
        HOUR = str( hex( int(gps.timestamp[0]) )[2:] ).zfill(2)
        MIN  = str( hex( int(gps.timestamp[1]) )[2:] ).zfill(2)
        SEC  = str( hex( int(gps.timestamp[2]) )[2:] ).zfill(2)
        TIME = (HOUR + MIN + SEC)


        str1 = (TIME + LATI + LON + ALT + SPD + CRS)
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
        str2 = f'AT+SENDB=01,03,15,{str1}\n'
        str2=str2.encode(encoding = "UTF-8")
        print(str2)
        ser.write(str2)
        time.sleep(20.0)