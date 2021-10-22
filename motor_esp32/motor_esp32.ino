const int leftFout = 18; 
const int leftBout = 5; 
const int rightFout = 19; 
const int rightBout = 21; 

// setting PWM properties
const int freq = 5000;
const int leftF = 0;
const int leftB = 1;
const int rightF = 2;
const int rightB = 3;
const int resolution = 8;
 
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

  Serial.begin(115200); 
}

void allStop() {
  ledcWrite(leftF, 0);
  ledcWrite(leftB, 0);
  ledcWrite(rightF, 0);
  ledcWrite(rightB, 0);
}
 
void loop(){
  if(Serial.available()){
    int turningSpeed = 100;
    int aheadSpeed = 100;
    String command = Serial.readStringUntil('\n');
    Serial.printf("Command received %s \n", command);
    if (command.equals("left")) {
      allStop();
      ledcWrite(leftF, turningSpeed);
      ledcWrite(rightB, turningSpeed);
    } else if (command.equals("right")) {
      allStop();
      ledcWrite(rightF, turningSpeed);
      ledcWrite(leftB, turningSpeed);
    } else if (command.equals("stop")) {
      allStop();
    } else if (command.equals("ahead")) {
      allStop();
      ledcWrite(leftF, aheadSpeed);
      ledcWrite(rightF, aheadSpeed);
    }
  }
}
