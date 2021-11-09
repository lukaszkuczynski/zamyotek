#include <ESP32Servo.h>

const int leftB = 27;
const int leftF = 26; 
const int leftEnable = 25; 

const int rightB = 33;
const int rightF = 32; 
const int rightEnable = 13; 

//Servo leftServo;
int leftServoPin = 14;


// setting PWM properties
const int freq = 50;
const int leftMotor = 2;
const int rightMotor = 0;

const int servo = 4;

const int servoOpened = 5;
const int servoClosed = 30;



const int resolution = 8;

#define TURNING_TIME 250
#define STOP_TIME 100      

#define DEFAULT_SPEED "120"
 
void setup(){
    // Allow allocation of all timers
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  
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

  ledcSetup(servo, freq, resolution);
  ledcAttachPin(leftServoPin, servo);
//  leftServo.setPeriodHertz(50);    // standard 50 hz servo
//  leftServo.attach(leftServoPin, 500, 2400); 
//
  ledcWrite(servo, servoOpened);
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
    String full_command = Serial.readStringUntil('\n');
    int i1 = full_command.indexOf(',');
    int i2 = full_command.indexOf(',', i1+1);
    String cmd_arg = DEFAULT_SPEED;
    String command = full_command;
    if (i1 > 0) {
      command= full_command.substring(0, i1);
      cmd_arg = full_command.substring(i1+1);
    }
    int turningSpeed = cmd_arg.toInt();
    Serial.printf("Command received %s \n", command);
    if (command.equals("left")) {
      allStop();
      digitalWrite(leftB, HIGH);
      digitalWrite(rightF, HIGH);
      ledcWrite(leftMotor, turningSpeed);
      ledcWrite(rightMotor, turningSpeed);
      delay(TURNING_TIME);
      allStop();
      delay(STOP_TIME);
    } else if (command.equals("right")) {
      allStop();
      digitalWrite(leftF, HIGH);
      digitalWrite(rightB, HIGH);
      ledcWrite(leftMotor, turningSpeed);
      ledcWrite(rightMotor, turningSpeed);
      delay(TURNING_TIME);
      allStop();
      delay(STOP_TIME);
    } else if (command.equals("stop")) {
      allStop();
    } else if (command.equals("ahead")) {
      allStop();
      digitalWrite(leftF, HIGH);
      digitalWrite(rightF, HIGH);
      ledcWrite(leftMotor, turningSpeed);
      ledcWrite(rightMotor, turningSpeed);
    } else if (command.equals("open_gate")) {
      ledcWrite(servo, servoOpened);
    } else if (command.equals("close_gate")) {
      ledcWrite(servo, servoClosed);
//       leftServo.write(leftServoClosed);
    }
  }


}
