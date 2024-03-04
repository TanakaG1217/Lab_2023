//Stringをもう２００文字くらい使うとメモリ不足でバグる！！！！！！

#include <Adafruit_GPS.h>
#include <SoftwareSerial.h>

bool stringComplete = false;              // whether the string is complete
SoftwareSerial LA66_serial_port(10, 11);  // Arduino RX, TX ,

Adafruit_GPS GPS(&Wire);

void setup() {
  GPS.begin(0x10);  // The I2C address to use is 0x10
  LA66_serial_port.begin(9600);
  Serial.begin(9600);
}


//１０進数数値を任意の桁数の２進数文字列に変換
String toBinaryString(long dec, int len) {
  char cal_bin[len + 1];  // 配列のサイズを指定
  cal_bin[len] = '\0';    // 終端文字を設定
  // 2進数文字列を逆順で構築
  for (int i = len - 1; i >= 0; i--) {
    cal_bin[i] = (dec % 2) + '0';  // '0' または '1' を格納
    dec /= 2;
  }
  String Str_bynaried = String(cal_bin);  // char配列からStringへ変換

  return Str_bynaried;
}


String binaryToHex(String binaryString) {
  String hexString = "";
  // 80ビットの2進数文字列を処理するためのループ
  for (int i = 0; i < binaryString.length(); i += 4) {
    String fourBits = binaryString.substring(i, i + 4);
    int hexValue = 0;
    // 4ビットを1つの16進数に変換
    for (int j = 0; j < 4; j++) {
      hexValue |= (fourBits[j] == '1' ? 1 : 0) << (3 - j);
    }
    // 16進数の文字列に追加
    hexString += String(hexValue, HEX);
    //Serial.println(hexString);
  }

  return hexString;
}

static unsigned long lastTime = 0;  // 最後に処理を行った時間を保存する変数
unsigned long interval = 60000;     // 実行間隔をミリ秒単位で設定（30秒）

void loop() {
  unsigned long currentTime = millis();
  char c = GPS.read();
  if (currentTime - lastTime >= interval) {
    if (GPS.newNMEAreceived()) {
      // GPSセンテンスを解析
      if (GPS.parse(GPS.lastNMEA())) {

        if (GPS.latitude == 0) {
          Serial.print("GPS.latitude is 0. skip this turn.\n");
          lastTime = currentTime;
          delay(10000);
          return;
        }

        // 解析成功
        // GPSデータの取得
        double latitude = GPS.latitude / 100;
        double longitude = GPS.longitude / 100;
        int speed = (int)GPS.speed;
        int altitude = (int)GPS.altitude;
        int hour=(int)GPS.hour+9;
        int min = (int)GPS.minute;
        int sec = (int)GPS.seconds;

        if (hour >= 24){
          hour = hour-24;
        }
        min = (hour*60) +min;


        Serial.print("Latitude: ");
        Serial.println(latitude, 5);
        Serial.print("longitude: ");
        Serial.println(longitude, 5);
        Serial.print("speed: ");
        Serial.println(speed);
        Serial.print("altitude: ");
        Serial.println(altitude);
        Serial.print("min: ");
        Serial.println(min);
        Serial.print("sec: ");
        Serial.println(sec);


        //以下処理部
        int lati_int = (int)latitude - 20;
        long lati_flt = ((latitude - (int)latitude) * 500000/3);
        int lon_int = (int)longitude - 120;
        long lon_flt = ((longitude - (int)longitude) * 500000/3);

        Serial.println(lati_int);
        Serial.println(lati_flt);
        Serial.println(lon_int);
        Serial.println(lon_flt);

        // 2進数変換（例として、緯度と経度は10ビット、速度は5ビット、高度と衛星数は4ビットで表現）
        toBinaryString(12345678, 20);
        String binaryData;
        binaryData += "000";  //88bitになるように
        binaryData += toBinaryString(min, 11);
        binaryData += toBinaryString(sec, 6);
        binaryData += toBinaryString(lati_int, 5);
        Serial.println(lati_flt);
        binaryData += toBinaryString(lati_flt, 17);
        binaryData += toBinaryString(lon_int, 5);
        Serial.println(lon_flt);
        binaryData += toBinaryString(lon_flt, 17);
        binaryData += toBinaryString(altitude, 8);
        binaryData += toBinaryString(speed, 7);
        binaryData += "000000001";  //コース実装予定

        Serial.println(binaryData);



        // 前のステップで得られた binaryData を使用
        String hexData = binaryToHex(binaryData);
        // 16進数データの出力
        Serial.println(hexData);
        Serial.println("printed hex");


        String tx_msg = "AT+SENDB=01,03,11," + hexData + "\r\n";
        LA66_serial_port.print(tx_msg);
        Serial.print(tx_msg);

        lastTime = currentTime;
        //delay(40000);
      }
    }
  }
}