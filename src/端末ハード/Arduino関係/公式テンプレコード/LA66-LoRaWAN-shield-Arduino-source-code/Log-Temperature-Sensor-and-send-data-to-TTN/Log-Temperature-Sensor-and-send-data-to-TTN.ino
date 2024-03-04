#include <SoftwareSerial.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>
/*

*/
#define DHTPIN 8                 // Digital pin connected to the DHT sensor 
#define DHTTYPE    DHT11         // DHT 11
DHT_Unified dht(DHTPIN, DHTTYPE);

String inputString = "";         // a String to hold incoming data
bool stringComplete = false;     // whether the string is complete

long old_time=millis();
long new_time;

long uplink_interval=30000;      //ms

bool time_to_at_recvb=false;
bool get_LA66_data_status=false;

bool network_joined_status=false;

float DHT11_temp;
float DHT11_hum;

SoftwareSerial ss(10, 11);       // Arduino RX, TX ,

char rxbuff[128];
uint8_t rxbuff_index=0;

void setup() {
  // initialize serial
  Serial.begin(9600);

  ss.begin(9600);
  ss.listen();
  
  // reserve 200 bytes for the inputString:
  inputString.reserve(200);

  dht.begin();
  sensor_t sensor;
  dht.temperature().getSensor(&sensor);
  dht.humidity().getSensor(&sensor);
  
  ss.println("ATZ");//reset LA66
}

void loop() {

  new_time = millis();

  if((new_time-old_time>=uplink_interval)&&(network_joined_status==1)){
    old_time = new_time;
    get_LA66_data_status=false;

  // Get temperature event and print its value.
  sensors_event_t event;
  dht.temperature().getEvent(&event);
  if (isnan(event.temperature)) {
    Serial.println(F("Error reading temperature!"));
    DHT11_temp=327.67;
  }
  else {
    DHT11_temp=event.temperature;
    
    if(DHT11_temp>60){
      DHT11_temp=60;
    }
    else if(DHT11_temp<-20){
      DHT11_temp=-20;
    }
  }
  // Get humidity event and print its value.
  dht.humidity().getEvent(&event);
  if (isnan(event.relative_humidity)) {
    DHT11_hum=327.67;
    Serial.println(F("Error reading humidity!"));
  }
  else {
    DHT11_hum=event.relative_humidity;
    
    if(DHT11_hum>100){
      DHT11_hum=100;
    }
    else if(DHT11_hum<0){
      DHT11_hum=0;
    }
  }

    Serial.print(F("Temperature: "));
    Serial.print(DHT11_temp);
    Serial.println(F("°C"));
    Serial.print(F("Humidity: "));
    Serial.print(DHT11_hum);
    Serial.println(F("%"));
    
    char sensor_data_buff[128]="\0";

    //confirm status,Fport,payload length,payload(HEX)
    snprintf(sensor_data_buff,128,"AT+SENDB=%d,%d,%d,%02X%02X%02X%02X",0,2,4,(short)(DHT11_temp*100)>>8 & 0xFF,(short)(DHT11_temp*100) & 0xFF,(short)(DHT11_hum*10)>>8 & 0xFF,(short)(DHT11_hum*10) & 0xFF);
    ss.println(sensor_data_buff);
  }

  if(time_to_at_recvb==true){
    time_to_at_recvb=false;
    get_LA66_data_status=true;
    delay(1000);
    
    ss.println("AT+CFG");    
  }

    while ( ss.available()) {
    // get the new byte:
    char inChar = (char) ss.read();
    // add it to the inputString:
    inputString += inChar;

    rxbuff[rxbuff_index++]=inChar;

    if(rxbuff_index>128)
    break;
    
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n' || inChar == '\r') {
      stringComplete = true;
      rxbuff[rxbuff_index]='\0';
      
      if(strncmp(rxbuff,"JOINED",6)==0){
        network_joined_status=1;
      }

      if(strncmp(rxbuff,"Dragino LA66 Device",19)==0){
        network_joined_status=0;
      }

      if(strncmp(rxbuff,"Run AT+RECVB=? to see detail",28)==0){
        time_to_at_recvb=true;
        stringComplete=false;
        inputString = "\0";
      }

      if(strncmp(rxbuff,"AT+RECVB=",9)==0){       
        stringComplete=false;
        inputString = "\0";
        Serial.print("\r\nGet downlink data(FPort & Payload) ");
        Serial.println(&rxbuff[9]);
      }
      
      rxbuff_index=0;

      if(get_LA66_data_status==true){
        stringComplete=false;
        inputString = "\0";
      }
    }
  }

   while ( Serial.available()) {
    // get the new byte:
    char inChar = (char) Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n' || inChar == '\r') {
      ss.print(inputString);
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
