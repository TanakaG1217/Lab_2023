#include <Adafruit_GPS.h>
#include <BigNumber.h>

Adafruit_GPS GPS(&Wire);

void setup() {
  while (!Serial) {}
  Serial.begin(115200);
  Serial.println("Adafruit GPS library basic I2C test!");
  GPS.begin(0x10);       // The I2C address to use is 0x10
  BigNumber::begin(90);  // 20桁の精度を指定
}

String toBinaryString(long number, int bits) {
  String binaryStr = "";
  for (int i = 0; i < bits; i++) {
    binaryStr = String(number % 2) + binaryStr;
    number = number / 2;
  }
  return binaryStr;
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
  }
  while (hexString.length() < 22) {
        hexString = "0" + hexString;
  }
  
  return hexString;
}



void loop() {
  //Serial.println("始まり");
  char c = GPS.read();
  //printf(c);
  // GPSデータが利用可能かチェック
  if (GPS.newNMEAreceived()) {
    // GPSセンテンスを解析
    if (GPS.parse(GPS.lastNMEA())) {
      // 解析成功
      // GPSデータの取得
      double latitude = GPS.latitude / 100;
      double longitude = GPS.longitude / 100;
      int speed = (int)GPS.speed;
      int altitude = (int)GPS.altitude;
      int min = (int)GPS.hour * 60 + (int)GPS.minute;
      int sec = (int)GPS.seconds;
      /*
      Serial.print("Latitude: ");
      Serial.println(latitude,5);
      Serial.print("longitude: ");
      Serial.println(longitude,5);
      Serial.print("speed: ");
      Serial.println(speed);
      Serial.print("altitude: ");
      Serial.println(altitude);
      Serial.print("min: ");
      Serial.println(min);
      Serial.print("sec: ");
      Serial.println(sec);
      */

      //以下処理部
      int lati_int =(int)latitude - 20;
      long lati_flt = ((latitude - (int)latitude)*100000);
      int lon_int= (int)longitude - 120;
      long lon_flt = ((longitude - (int)longitude)*100000);
      // 2進数変換（例として、緯度と経度は10ビット、速度は5ビット、高度と衛星数は4ビットで表現）
      String binaryData = "";
      binaryData += "000"; //88bitになるように
      binaryData += toBinaryString(min, 11);
      binaryData += toBinaryString(sec, 6);
      binaryData += toBinaryString(lati_int, 5);
      binaryData += toBinaryString(lati_flt, 17);
      binaryData += toBinaryString(lon_int,5);
      binaryData += toBinaryString(lon_flt, 17);
      binaryData += toBinaryString(altitude, 8);
      binaryData += toBinaryString(speed, 7);
      binaryData += "000000000"; //コース実装予定
      //Serial.println(binaryData);

      // 前のステップで得られた binaryData を使用
      String hexData = binaryToHex(binaryData);
      // 16進数データの出力
      //Serial.println(hexData);


      
    }
  }
}