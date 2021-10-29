#include <ArduinoJson.h>

const int leftFout = 18; 
const int leftBout = 5; 
const int rightFout = 19; 
const int rightBout = 21; 

const int DISTANCE_SENSOR_PIN = 4;

// setting PWM properties
const int freq = 50;
const int leftF = 0;
const int leftB = 1;
const int rightF = 2;
const int rightB = 3;
const int resolution = 8;

#define TURNING_TIME 150
#define STOP_TIME 100      
 
void setup(){
  // configure LED PWM functionalitites
  ledcSetup(leftF, freq, resolution);
  ledcSetup(leftB, freq, resolution);
  ledcSetup(rightF, freq, resolution);
  ledcSetup(rightB, freq, resolution);
  
  // attach the channel to the GPIO to be controlled
  ledcAttachPin(leftFout, leftF);
  ledcAttachPin(leftBout, leftB);
  ledcAttachPin(rightFout, rightF);
  ledcAttachPin(rightBout, rightB);

  pinMode(DISTANCE_SENSOR_PIN, INPUT);

  Serial.begin(115200); 
}


DynamicJsonDocument msg(1024);

void allStop() {
  ledcWrite(leftF, 0);
  ledcWrite(leftB, 0);
  ledcWrite(rightF, 0);
  ledcWrite(rightB, 0);
}

void loop(){
  if(Serial.available()){
    int turningSpeed = 80;
    int aheadSpeed = 80;
    String command = Serial.readStringUntil('\n');
    Serial.printf("Command received %s \n", command);
    if (command.equals("left")) {
      allStop();
      ledcWrite(leftF, turningSpeed);
      ledcWrite(rightB, turningSpeed);
      delay(TURNING_TIME);
      allStop();
      delay(STOP_TIME);
    } else if (command.equals("right")) {
      allStop();
      ledcWrite(rightF, turningSpeed);
      ledcWrite(leftB, turningSpeed);
      delay(TURNING_TIME);
      allStop();
      delay(STOP_TIME);
    } else if (command.equals("stop")) {
      allStop();
    } else if (command.equals("ahead")) {
      allStop();
      ledcWrite(leftF, aheadSpeed);
      ledcWrite(rightF, aheadSpeed);
    }
  }


  msg["topic"] = "distance";
  msg["millis"]   =  millis();
  msg["distance"] = digitalRead(DISTANCE_SENSOR_PIN);


  serializeJson(msg, Serial);
  Serial.println("");

//  for (int i = 0; i < 100 ; i=i+3) {
//    Serial.printf("speed %d \n", i);
//    ledcWrite(leftF, i);
//    ledcWrite(rightF, i);  
//    delay(1000);
//  }
  

}
