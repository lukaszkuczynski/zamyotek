#include <ArduinoJson.h>


#define echoPin 18 // Echo Pin
#define trigPin 2 // Trigger Pin
 
long duration, distance; // Duration used to calculate distance

DynamicJsonDocument msg(1024);

 
void setup()
{
  Serial.begin(115200);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}
 
void loop()
{
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  //Calculate the distance (in cm) based on the speed of sound.
  distance = duration/58.2;
  msg["topic"] = "distance";
  msg["millis"]   =  millis();
  msg["distance"] = distance;
  serializeJson(msg, Serial);
  Serial.println("");
  //Delay 50ms before next reading.
  delay(100);
}
