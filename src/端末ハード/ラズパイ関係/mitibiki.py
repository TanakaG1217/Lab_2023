import serial
import micropyGPS
import threading
import time

gps = micropyGPS.MicropyGPS(9, 'dd') # MicroGPSオブジェクトを生成する。
                                     # 引数はタイムゾーンの時差と出力フォーマッ ト

def rungps(): # GPSモジュールを読み、GPSオブジェクトを更新する
    s = serial.Serial('/dev/serial0', 9600, timeout=10)
    s.readline() # 最初の1行は中途半端なデーターが読めることがあるので、捨てる
    while True:
        sentence = s.readline().decode('utf-8') # GPSデーターを読み、文字列に変 換する
        if sentence[0] != '$': # 先頭が'$'でなければ捨てる
            continue
        for x in sentence: # 読んだ文字列を解析してGPSオブジェクトにデーターを追加、更新する
            gps.update(x)

gpsthread = threading.Thread(target=rungps, args=()) # 上の関数を実行するスレッ ドを生成
gpsthread.daemon = True
gpsthread.start() # スレッドを起動

while True:
    if gps.clean_sentences > 20: # ちゃんとしたデーターがある程度たまったら出力 する
        h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
        print('%2d:%02d:%04.1f' % (h, gps.timestamp[1], gps.timestamp[2]))
        print('緯度経度: %2.8f, %2.8f' % (gps.latitude[0], gps.longitude[0]))
        print('緯度' , gps.latitude, '経度' , gps.longitude)
        print('海抜: %f' % gps.altitude)
        print('使用衛星:' , gps.satellites_used)
        print('衛星番号: (仰角, 方位角, SN比)')
        for k, v in gps.satellite_data.items():
            print('%d: %s' % (k, v))
        print('')
        print("航行方向: %f" %gps.course)
        print('速度: %f' %gps.speed[2] )
    time.sleep(3.0)