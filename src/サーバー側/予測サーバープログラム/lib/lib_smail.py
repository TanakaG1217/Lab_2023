import smtplib
from email.mime.text import MIMEText
import datetime

def main(datas, config):
    #本文の編集
    message = str(datas["JPtime"].year) + '年' + str(datas["JPtime"].month) + '月' + str(datas["JPtime"].day) + '日' + str(datas["JPtime"].hour) + '時' + str(datas["JPtime"].minute) + '分' + "<br>" + "部屋番号：" +str(datas["number"]) + "<br>" + "CO2濃度：" + str(datas["PPM"]) + "<br>" + "http://133.71.106.168/s/co2/app/dashboards#/"# メール本文
    msg = MIMEText(message, "html")
    #件名の編集
    msg["Subject"] = datas["number"] + "が1000PPMを超えました"
    #メール送信元
    msg["From"] = config["From_mail"]["From"]
    # サーバを指定する
    server = smtplib.SMTP(config["From_mail"]["server_DN"], config["From_mail"]["port"])

    #送信先へforループで複数のメールアドレスに送信
    for To in config["To_mail"]["To"]:
        msg["To"] = To
        # メールを送信する
        server.send_message(msg)
        # 閉じる
        server.quit()
