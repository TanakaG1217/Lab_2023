from email import header
import minimalmodbus
import datetime
import ipget
import schedule
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import os
import csv
import time
import glob
import dateutil.parser
from pathlib import Path
import configparser
#メール送信用
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
import logging


#modbusの設定
instrument = minimalmodbus.Instrument("/dev/ttyUSB0",1,minimalmodbus.MODE_RTU);#/dev/serial1',1);#0',1);#/dev/ttyUSB1', 1)  # port name, slave address (in decimal)
instrument.serial.parity = minimalmodbus.serial.PARITY_ODD;
instrument.debug=True;
instrument.handle_local_echo = False #　echo backするデバイス時はTrueに設定
close_port_after_each_call = True #　通信ごとに毎回ポートのopen/closeを行う場合はTrueに設定
instrument.mode = minimalmodbus.MODE_RTU  # モード設定　minimalmodbus.MODE_RTU or minimalmodbus.MODE_ACSII
instrument.serial.timeout = 0.5  # タイムアウト時間(s)


#CO2センサーからデータ取得プログラム
def MODBUS(datas_):
    error_code = None
    try:
        #CO2センサーから値の取得
        PPM = instrument.read_register(68, number_of_decimals=0, functioncode=3, signed=False); # Registernumber 68(deci.)=0044H, number of decimals PPM
        TEMP = instrument.read_register(69, 2)  # Registernumber =0045H, number of decimals 2
        RH = instrument.read_register(70, 2)  # Registernumber 0046H, number of decimals 2
        if PPM == 65535 or RH == 655.35 or TEMP == 655.35: #データ受信時に「1111.1111.1111.1111」を受信した場合
            PPM = TEMP = RH = None
        datas_.update(PPM=PPM, TEMP=TEMP, RH=RH)
    except minimalmodbus.InvalidResponseError as error_code: #数値の読み込み不可
        pass
    except minimalmodbus.NoResponseError as error_code: #電源off
        pass
    except Exception as error_code: #その他のエラー
        pass
    return datas_, error_code
