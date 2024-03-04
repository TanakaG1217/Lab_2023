function Decoder(bytes, port) {
    var byte = bytes;
    
    var DATAs ='';
    //受信データバイナリデータ
    for (var i = 0; i < 11; i++) {
      var BYTE_bin = bytes[i].toString(2).padStart(8,'0');
      DATAs = DATAs + BYTE_bin;
    }
    
    function getBit(binaryString, start, end) {
      let extractedSubstring = "";
      // 指定範囲の部分文字列を取得
      for (let i = start; i <= end; i++) {
        extractedSubstring += binaryString[i];
      }
      // 取得した部分文字列を10進数に変換
      const decimalValue = parseInt(extractedSubstring, 2);
      return decimalValue;
    }
    
    var time = getBit(DATAs,3,13);
    var hour = parseInt(time/60);
    var min  = time%60;
    var sec  = getBit(DATAs,14,19);
    
    var latitude_int = getBit(DATAs,20,24) +20;
    var latitude_flt = getBit(DATAs,25,41) /100000;
    var latitude     = latitude_int + latitude_flt;
    
    var longitude_int= getBit(DATAs,42,46) +120;
    var longitude_flt= getBit(DATAs,47,63) /100000;
    var longitude    = longitude_int + longitude_flt;
    
    var alt          = getBit(DATAs,64,71);
    var speed        = getBit(DATAs,72,78);
    var course       = getBit(DATAs,79,87);
    
    
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