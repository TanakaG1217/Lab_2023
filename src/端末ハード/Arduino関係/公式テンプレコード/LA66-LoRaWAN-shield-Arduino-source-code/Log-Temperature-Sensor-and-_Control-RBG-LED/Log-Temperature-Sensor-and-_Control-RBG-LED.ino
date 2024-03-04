#include <SoftwareSerial.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>
/*

*/
#define DHTPIN 8                 // Digital pin connected to the DHT sensor 
#define DHTTYPE    DHT11         // DHT 11
DHT_Unified dht(DHTPIN, DHTTYPE);
//Define macros
#define ON 1
#define OFF 0
 
//Define RGB_LED pin
int LED_R = 13;
int LED_G = 12;
int LED_B = 9;
/* A hexadecimal number is converted to a decimal number */
long hexToDec(char *source);
 
/* Returns the sequence number of the ch character in the sign array */
int getIndexOfSigns(char ch);

String inputString = "";         // a String to hold incoming data
bool stringComplete = false;     // whether the string is complete

long old_time=millis();
long new_time;

long uplink_interval=30000;      //ms

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
  // Initializes the IO port of RGB three-color LED as the output mode
  pinMode(LED_R,OUTPUT);
  pinMode(LED_G,OUTPUT);
  pinMode(LED_B,OUTPUT);
}
void color_led(int v_iRed, int v_iGreen, int v_iBlue)
{
  //Red LED
  if (v_iRed == ON)
  {
    digitalWrite(LED_R,HIGH);
    }
  else
  {
    digitalWrite(LED_R,LOW);
    }
  //Green LED
  if (v_iGreen == ON)
  {
    digitalWrite(LED_G,HIGH);
    }
  else
  {
    digitalWrite(LED_G,LOW);
    }   
  //Blue LED
  if (v_iBlue == ON)
  {
    digitalWrite(LED_B,HIGH);
    } 
  else
  {
    digitalWrite(LED_B,LOW);
    }
  }
long hexToDec(char *source)
{
    long sum = 0;
    long t = 1;
    int i, len;
 
    len = strlen(source);
    for(i=len-1; i>=0; i--)
    {
        sum += t * getIndexOfSigns(*(source + i));
        t *= 16;
    }  
 
    return sum;
}
/* Returns the sequence number of the ch character in the sign array */
int getIndexOfSigns(char ch)
{
    if(ch >= '0' && ch <= '9')
    {
        return ch - '0';
    }
    if(ch >= 'A' && ch <='F') 
    {
        return ch - 'A' + 10;
    }
    if(ch >= 'a' && ch <= 'f')
    {
        return ch - 'a' + 10;
    }
    return -1;
}

void loop() {

    while ( ss.available()) {
    // get the new byte:
    char inChar = (char) ss.read();
    // add it to the inputString:
    inputString += inChar;

    rxbuff[rxbuff_index++]=inChar;

    if(rxbuff_index>128)
    {
      rxbuff[rxbuff_index]='\0';    
      rxbuff_index=0;      
      break;
    }
    
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n' || inChar == '\r') {
      stringComplete = true;
      rxbuff[rxbuff_index]='\0'; 
      if(strncmp(rxbuff,"LA66 P2P",8)==0){
                                   //LED_R    LED_G    LED_B  colour
         color_led(ON, ON, ON);   //   1        1        1    linght off
      }
      if(strncmp(rxbuff,"Data: (HEX:) 30 31 30 31 30 31",30)==0){      //When LA66 sheild receives 010101, the RGB_LED is turned off
                                   //LED_R    LED_G    LED_B  colour
         color_led(ON, ON, ON);   //   1        1        1    linght off
      }
      if(strncmp(rxbuff,"Data: (HEX:) 30 31 30 31 30 30",30)==0){      //When LA66 sheild receives 010100, the RGB_LED is Green
                                   //LED_R    LED_G    LED_B  
         color_led(ON, ON, OFF);   //   1        1        0   Green
      }
      if(strncmp(rxbuff,"Data: (HEX:) 30 31 30 30 30 31",30)==0){
                                   //LED_R    LED_G    LED_B  
         color_led(ON, OFF, ON);   //   1        0        1  Blue
      }
      if(strncmp(rxbuff,"Data: (HEX:) 30 30 30 31 30 31",30)==0){
                                   //LED_R    LED_G    LED_B
         color_led(OFF, ON, ON);   //   0        1        1  Red
      }
      if(strncmp(rxbuff,"Data: (HEX:) 30 30 30 30 30 31",30)==0){
                                   //LED_R    LED_G    LED_B
         color_led(OFF, OFF, ON);   //   0        0        1  purple
      }
      if(strncmp(rxbuff,"Data: (HEX:) 30 30 30 31 30 30",30)==0){
                                   //LED_R    LED_G    LED_B
         color_led(OFF, ON, OFF);   //   0        1        0  Yellow
      }
      if(strncmp(rxbuff,"Data: (HEX:) 30 31 30 30 30 30",30)==0){
                                   //LED_R    LED_G    LED_B
         color_led(ON, OFF, OFF);   //   1        0        0  Wathet blue
      }
      if(strncmp(rxbuff,"Data: (HEX:) 30 30 30 30 30 30",30)==0){
                                   //LED_R    LED_G    LED_B
         color_led(OFF, OFF, OFF);  //   0        0        0 white
      }
      
      rxbuff_index=0;
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
  
  new_time = millis();

  if(new_time-old_time>=uplink_interval){
    old_time = new_time;

  Serial.print(F("\r\n"));
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
    Serial.print(F("\r\n"));
    
    char sensor_data_buff[128]="\0";
    char tem[5]="\0";
    char hum[5]="\0";
    snprintf(tem,5,"%02X%02X",(short)(DHT11_temp*100)>>8 & 0xFF,(short)(DHT11_temp*100) & 0xFF);
    snprintf(hum,5,"%02X%02X",(short)(DHT11_hum*100)>>8 & 0xFF,(short)(DHT11_hum*100) & 0xFF);
    //Parameter 1: send hex or text 0: Send hex 1: Send text
    //Parameter 2: Content
    //Parameter 3: ACK Type 0:  No ACK 1:  Wait for ACK (Same as what we sent) 2:  Wait for ACK ( 0x00 FF)
    //Parameter 4 : Retransmission ( 0 ~ 8 )
    snprintf(sensor_data_buff,128,"AT+SEND=1,tem=%ld hum=%ld,0,0",hexToDec(tem)/100,hexToDec(hum)/100);
    ss.print(sensor_data_buff);
    ss.print('\r');
  }
  
}
