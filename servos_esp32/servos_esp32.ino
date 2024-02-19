#include <ESP32Servo.h>
#include <Adafruit_NeoPixel.h>

int leftServoPin = 4;
int rightServoPin = 26;

const int NEOPIXEL_PIN = 23;
const int NEOPIXEL_LED_COUNT = 8;

const int freq = 50;
const int resolution = 8;

const int leftServoOpened = 110;
const int leftServoClosed = 30;


const String DEFAULT_DEGREE = "0";

const int steps = 10;
const int stepDelay = 50;

Servo leftServo;
Servo rightServo;

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(NEOPIXEL_LED_COUNT, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);
 
void setup(){
  leftServo.setPeriodHertz(50);    // standard 50 hz servo
  leftServo.attach(leftServoPin, 500, 2400); 
  rightServo.setPeriodHertz(50);    // standard 50 hz servo
  rightServo.attach(rightServoPin, 500, 2400); 
  Serial.begin(115200);
  pixels.begin();
  closeGate();
}

void openGate() {
  int step_size = abs(leftServoClosed - leftServoOpened) / steps;
  for (int pos=leftServoClosed; pos<leftServoOpened; pos+=step_size) {
    leftServo.write(pos);  
    delay(stepDelay);
  }
}

void closeGate() {
  int step_size = abs(leftServoClosed - leftServoOpened) / steps;
  for (int pos=leftServoOpened; pos>leftServoClosed; pos-=step_size) {
    leftServo.write(pos);  
    delay(stepDelay);
  }
  
  leftServo.write(leftServoClosed);
//  rightServo.write(rightServoClosed);  
}

void setColor(String color) {
  Serial.printf("Setting color to %s\n", color);
  int r = 0;
  int g = 0;
  int b = 0;
  if (color == "green") {
    g = 255;  
  } else if (color == "red") {
    r = 255;
  } else if (color == "orange") {
    r = 255;
    g = 165;
  } else if (color == "white") {
    r = 255;
    g = 255;
    b = 255;
  } else if (color == "blue") {
    r = 50;
    g = 100;
    b = 255;
  } else {
    // black is fallback
  }
  for (int k = 0; k < NEOPIXEL_LED_COUNT; k++) {
    pixels.setPixelColor(k, pixels.Color(r, g, b));
  }
  pixels.show();
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
    if (command.equals("open_gate") || command.equals("godown")) {
      openGate();
      Serial.println("godown finished");
    } else if ((command.equals("close_gate") || command.equals("goup"))) {
      closeGate();
      Serial.println("goup finished");
    }
    if (command.equals("setColor")) {
      setColor(cmd_arg);
    }
  }
}
