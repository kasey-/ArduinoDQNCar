#include <SoftwareSerial.h>  
#define RX_PIN 2
#define TX_PIN 3
SoftwareSerial bluetooth(RX_PIN,TX_PIN);

long cmpt;

void setup() {  
  pinMode(RX_PIN, INPUT);  
  pinMode(TX_PIN, OUTPUT);  
  bluetooth.begin(115200);
  
  Serial.begin(115200);
  Serial.println("Proxy Ready");
}  

void loop() {
  bluetooth.println(cmpt);  
  cmpt++;
  delay(100);
}  
