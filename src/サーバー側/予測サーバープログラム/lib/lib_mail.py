from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
import logging
import socket

#メール送信プログラム
def MAIL(data):
    try:
        dt = datetime.datetime.now()
        week = dt.strftime('%a')
        minute = dt.minute + 60 * dt.hour
        #if week != "Sun" and week != "Sat" and minute >= 510 and minute <= 1020: #日曜以外，土曜以外，8:00以上，17:00未満
        if week != "Sun" and week != "Sat": #日曜以外，土曜以外
            year = str(dt.year)
            month = str(dt.month)
            day = str(dt.day)
            hour = str(dt.hour)
            minute = str(dt.minute)

            sender, password = "modbusrh@gmail.com", "Modbus2020" # 送信元メールアドレスとgmailへのログイン情報
            #to = 'syogo_614@yahoo.co.jp' # 送信先メールアドレス
            sub = number + "が1000PPMを超えました"    #メール件名
            body = year + '年' + month + '月' + day + '日' + hour + '時' + minute + '分' + "\r\n" + "部屋番号:" + number + "\r\n" + "CO2濃度:" + str(PPM) + "\r\n" + "http://133.71.106.168/s/co2/app/dashboards#/"# メール本文
            host, port = 'smtp.gmail.com', 587

            # メールヘッダー
            msg = MIMEMultipart()
            msg['Subject'] = sub
            msg['From'] = sender
            msg['To'] = to

            # メール本文
            body = MIMEText(body)
            msg.attach(body)

            # gmailへ接続(SMTPサーバーとして使用)
            gmail=SMTP("smtp.gmail.com", 587)
            gmail.starttls() # SMTP通信のコマンドを暗号化し、サーバーアクセスの認証を通す
            gmail.login(sender, password)
            gmail.send_message(msg)

    except Exception as e:
        pass