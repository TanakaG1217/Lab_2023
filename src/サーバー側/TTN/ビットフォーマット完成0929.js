function Decoder(bytes, port) {
  //TTNはデバイスからの受信メッセージを１バイト毎の配列で渡してくる．

  var DATAs ='';
  //受信したバイト配列をビット文字列へ
  for (var i = 0; i < 11; i++) {
    var BYTE_bin = bytes[i].toString(2).padStart(8,'0');
    DATAs = DATAs + BYTE_bin;
  }
  
   // ビット文字列から範囲を指定し，10進数へ変換
  function decodeBitToDec(binaryString, start, end) {
    let extractedSubstring = "";
    for (let i = start; i <= end; i++) {
      extractedSubstring += binaryString[i];
    }
    const decimalValue = parseInt(extractedSubstring, 2);
    return decimalValue;
  }
  
  var time = decodeBitToDec(DATAs,3,13);
  var hour = parseInt(time/60);
  var min  = time%60;
  var sec  = decodeBitToDec(DATAs,14,19);
  
  var latitude_int = decodeBitToDec(DATAs,20,24) +20;
  var latitude_flt = decodeBitToDec(DATAs,25,41) /100000;
  var latitude     = latitude_int + latitude_flt;
  
  var longitude_int= decodeBitToDec(DATAs,42,46) +120;
  var longitude_flt= decodeBitToDec(DATAs,47,63) /100000;
  var longitude    = longitude_int + longitude_flt;
  
  var alt          = decodeBitToDec(DATAs,64,71);
  var speed        = decodeBitToDec(DATAs,72,78);
  var course       = decodeBitToDec(DATAs,79,87);
  
  
  return {
      byte: bytes,
      STR2: DATAs,
      time: {
          hour: hour,
          min: min,
          sec: sec
      },
      latitude: latitude,
      longitude: longitude,
      alt: alt,
      speed: speed,
      course: course
  };
}