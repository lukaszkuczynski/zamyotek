#include <ESP32Servo.h>

int leftServoPin = 25;
int rightServoPin = 26;

const int freq = 50;
const int resolution = 8;

const int leftServoOpened = 90;
const int leftServoClosed = 45;

const int rightServoOpened = 90;
const int rightServoClosed = 135;

const String DEFAULT_DEGREE = "0";

Servo leftServo;
Servo rightServo;
 
void setup(){
  leftServo.setPeriodHertz(50);    // standard 50 hz servo
  leftServo.attach(leftServoPin, 500, 2400); 
  rightServo.setPeriodHertz(50);    // standard 50 hz servo
  rightServo.attach(rightServoPin, 500, 2400); 
  Serial.begin(115200);
  openGate();
}

void openGate() {
  leftServo.write(leftServoOpened);
  rightServo.write(rightServoOpened);  
}

void closeGate() {
  leftServo.write(leftServoClosed);
  rightServo.write(rightServoClosed);  
}

void loop(){
  if(Serial.available()){
    String full_command = Serial.readStringUntil('\n');
    int i1 = full_command.indexOf(',');
    int i2 = full_command.indexOf(',', i1+1);
    String cmd_arg = DEFAULT_DEGREE;
    String command = full_command;
    if (i1 > 0) {
      command= full_command.substring(0, i1);
      cmd_arg = full_command.substring(i1+1);
    }
    int servoDegree = cmd_arg.toInt();
    Serial.printf("Command received %s \n", command);
    if (command.equals("open_gate")) {
      openGate();
    } else if (command.equals("close_gate")) {
      closeGate();
    }
  }
}
