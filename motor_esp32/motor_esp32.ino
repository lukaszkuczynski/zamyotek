#include <ESP32Servo.h>

const int leftB = 27;
const int leftF = 26; 
const int leftEnable = 25; 

const int rightB = 33;
const int rightF = 32; 
const int rightEnable = 19; 

Servo leftServo;
int leftServoPin = 20;


// setting PWM properties
const int freq = 30000;
const int leftMotor = 2;
const int rightMotor = 1;

const int stepper = 4;

const int leftServoOpened = 90;
const int leftServoClosed = 180;



const int resolution = 8;

#define TURNING_TIME 150
#define STOP_TIME 100      
 
void setup(){
  pinMode(leftF, OUTPUT);
  pinMode(leftB, OUTPUT);  
  pinMode(leftEnable, OUTPUT);  
 
  pinMode(rightF, OUTPUT);
  pinMode(rightB, OUTPUT);
  pinMode(rightEnable, OUTPUT);  
  
  // configure LED PWM functionalitites
  ledcSetup(leftMotor, freq, resolution);
  ledcSetup(rightMotor, freq, resolution);
  
  // attach the channel to the GPIO to be controlled
  ledcAttachPin(leftEnable, leftMotor);
  ledcAttachPin(rightEnable, rightMotor);

  leftServo.setPeriodHertz(50);    // standard 50 hz servo
  leftServo.attach(leftServoPin, 500, 2400); 

  leftServo.write(leftServoOpened);
  Serial.begin(115200); 
}



void allStop() {
  digitalWrite(leftF, 0);
  digitalWrite(leftB, 0);
  digitalWrite(rightF, 0);
  digitalWrite(rightB, 0);
}

void loop(){
  if(Serial.available()){
    int turningSpeed = 200;
    int aheadSpeed = 180;
    String command = Serial.readStringUntil('\n');
    Serial.printf("Command received %s \n", command);
    if (command.equals("left")) {
      allStop();
      digitalWrite(leftB, HIGH);
      digitalWrite(rightF, HIGH);
      ledcWrite(leftMotor, turningSpeed);
      ledcWrite(rightMotor, turningSpeed);
    } else if (command.equals("right")) {
      allStop();
      digitalWrite(leftF, HIGH);
      digitalWrite(rightB, HIGH);
      ledcWrite(leftMotor, turningSpeed);
      ledcWrite(rightMotor, turningSpeed);
    } else if (command.equals("stop")) {
      allStop();
    } else if (command.equals("ahead")) {
      allStop();
      digitalWrite(leftF, HIGH);
      digitalWrite(rightF, HIGH);
      ledcWrite(leftMotor, aheadSpeed);
      ledcWrite(rightMotor, aheadSpeed);
    } else if (command.equals("open_gate")) {
       leftServo.write(leftServoOpened);
    } else if (command.equals("close_gate")) {
       leftServo.write(leftServoClosed);
    }
  }


}
