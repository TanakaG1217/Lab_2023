#include <SoftwareSerial.h>
String inputString = "";      // a String to hold incoming data
bool stringComplete = false;  // whether the string is complete

SoftwareSerial LA66_serial_port(10, 11);  // Arduino RX, TX ,

void setup() {
  // initialize serial:
  LA66_serial_port.begin(9600);
  Serial.begin(9600);

  // reserve 200 bytes for the inputString:
  inputString.reserve(200);
}

void loop() {

  while (LA66_serial_port.available()) {
    // get the new byte:
    char inChar = (char)LA66_serial_port.read();
    // add it to the inputString:
    inputString += inChar;
    // if te incoming character is a newline, set a flag so the main loop can
    // do something abou t it:
    if (inChar == '\n' | inChar == '\r') {
      stringComplete = true;
    }
  }

  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if te incoming character is a newline, set a flag so the main loop can
    // do something abou t it:
    if (inChar == '\n' | inChar == '\r') {
      Serial.print(inputString);
      LA66_serial_port.print(inputString);
      //LA66_serial_port.print("AT+SENDB=01,03,11,087a86b1b318b49a0003ff\r\n");
      inputString = "\0";
    }
  }

  // print the string when a newline arrives:
  if (stringComplete) {
    Serial.print(inputString);

    // clear the string:
    inputString = "\0";
    stringComplete = false;
  }
}
