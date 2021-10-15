import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)  

motor_left_front = GPIO.PWM(12, 50)
motor_left_back = GPIO.PWM(16, 50)

motor_right_front = GPIO.PWM(13, 50)
motor_right_back = GPIO.PWM(26, 50)

    
class RpiMotorDriver:

    def __init__(self, turning_speed=50):
        self.stop()
        self.turning_speed = turning_speed


    def left(self):
        motor_left_front.ChangeDutyCycle(self.turning_speed)
        motor_left_back.ChangeDutyCycle(0)
        motor_right_front.ChangeDutyCycle(0)
        motor_right_back.ChangeDutyCycle(self.turning_speed)

    def right(self):
        motor_left_front.ChangeDutyCycle(0)
        motor_left_back.ChangeDutyCycle(self.turning_speed)
        motor_right_front.ChangeDutyCycle(self.turning_speed)
        motor_right_back.ChangeDutyCycle(0)

    def stop(self):
        motor_left_front.start(0)
        motor_left_back.start(0)
        motor_right_front.start(0)
        motor_right_back.start(0)


try:
    for speed in range(10,100,10):
        print(speed)
        driver = RpiMotorDriver(turning_speed=speed)
        print("go left!")
        driver.left()
        time.sleep(1)
        driver.stop()
        time.sleep(1)
        print("now right..")
        driver.right()
        time.sleep(2)
        driver.stop()
        time.sleep(1)
except KeyboardInterrupt:
    print('End of PWM-ing')
    GPIO.cleanup()
