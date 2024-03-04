import serial
import time
import threading
import micropyGPS
import math

gps = micropyGPS.MicropyGPS(9, 'dd') # MicroGPSオブジェクトを生成する。
                                     

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





while True:
    if gps.clean_sentences > 20: # ちゃんとしたデーターがある程度たまったら出力する
        h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
        
        print('緯度経度: %2.8f, %2.8f' % (gps.latitude[0], gps.longitude[0]))
        print('海抜: %f' % gps.altitude)

        lati = int(float(gps.latitude[0]))
        Lati = str(hex(int(lati)))[2:]
        lati_2 = int(float(gps.latitude[0]) * 100) % 100
        
        
        Lati_2 = str(hex(int(lati_2)))[2:]
        
        lati_decimal = math.modf(gps.latitude[0])[0]
        lati_4 = float(round(lati_decimal, 4))*10000
        lati_4_trunce = int(lati_4 // 100)*100
        lati_4_trunce = lati_4 - lati_4_trunce
        if lati_4_trunce < 10:
                Lati_4 = hex(int(lati_4_trunce))
                Lati_4 = int(Lati_4[2:])
                Lati_4 = format(Lati_4, "0=2")
        else:
                Lati_4 = hex((int(lati_4_trunce)))[2:]
        Lati_4 = str(Lati_4)
        
        
        lati_6 = float(round(lati_decimal, 6))*1000000
        lati_6_trunce = int(lati_6 // 100)*100
        lati_6_trunce = lati_6 - lati_6_trunce
        if lati_6_trunce < 10:
                Lati_6 = hex(int(lati_6_trunce))
                Lati_6 = int(Lati_6[2:])
                Lati_6 = format(Lati_6, "0=2")
        else:
                Lati_6 = hex((int(lati_6_trunce)))[2:]
        Lati_6 = str(Lati_6)
        
        lon = int(float(gps.longitude[0]))
        Lon = str(hex(int(lon)))[2:]
        
        lon_2 = int(float(gps.longitude[0]) * 100) % 100
        Lon_2 = str(hex(int(lon_2)))[2:]
        
        lon_decimal = math.modf(gps.longitude[0])[0]
        lon_4 = float(round(lon_decimal, 4))*10000
        lon_4_trunce = int(lon_4 // 100)*100
        lon_4_trunce = lon_4 - lon_4_trunce
        if lon_4_trunce < 10:
                Lon_4 = hex(int(lon_4_trunce))
                Lon_4 = int(Lon_4[2:])
                Lon_4 = format(Lon_4, "0=2")
        else:
                Lon_4 = hex((int(lon_4_trunce)))[2:]
        Lon_4 = str(Lon_4)
        
        lon_6 = float(round(lon_decimal, 6))*1000000
        lon_6_trunce = int(lon_6 // 100)*100
        lon_6_trunce = lon_6 - lon_6_trunce
        if lon_6_trunce < 10:
                Lon_6 = hex(int(lon_6_trunce))
                Lon_6 = int(Lon_6[2:])
                Lon_6 = format(Lon_6, "0=2")
        else:
                Lon_6 = hex((int(lon_6_trunce)))[2:]
        Lon_6 = str(Lon_6)
        
        alt= int(float(gps.altitude))
        Alt = str(hex(int(alt)))[2:]

        str1 = (Lati + Lati_2 + Lati_4 + Lon + Lon_2 + Lon_4 + Alt)
        ser = serial.Serial('/dev/ttyUSB0',)
        
        ser.baudrate = 9600
        ser.bytesize = 8
        ser.parity = 'N'
        ser.stopbits = 1
        ser.timeout = 10
        ser.xonxoff = 0
        ser.rtscts = 0

        str2 = f'AT+SENDB=01,03,07,{str1}\n'
        str2=str2.encode(encoding = "UTF-8")
        print(str2)
        ser.write(str2)
        ser.read()
        time.sleep(20.0)