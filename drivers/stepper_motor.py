import RPi.GPIO as GPIO
import time
from utils.logger import log


class StepperMotor:
    def __init__(
        self,
        step_pin=24,
        dir_pin=25,
        sleep_pin=23,
        motor_steps_per_rev=200,
        start_pos=0,
    ):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.sleep_pin = sleep_pin

        self.steps_per_rev = motor_steps_per_rev
        self.position = start_pos
        self.direction = True
        self.enabled = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.sleep_pin, GPIO.OUT)

        GPIO.output(self.sleep_pin, GPIO.HIGH)

        log("INFO", "STEPPER", "Stepper motor initialized")

    def enable(self):
        GPIO.output(self.sleep_pin, GPIO.LOW)
        self.enabled = True

    def disable(self):
        GPIO.output(self.sleep_pin, GPIO.HIGH)
        self.enabled = False
        log("INFO", "STEPPER", "Disabled motor")

    def set_direction(self, clockwise=True):
        GPIO.output(self.dir_pin, GPIO.HIGH if clockwise else GPIO.LOW)
        self.direction = clockwise

    def step(self, steps=1, delay=0.01):
        for _ in range(steps):
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(delay)
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay)

            if self.direction:
                self.position = (self.position + 1) % self.steps_per_rev
            else:
                self.position = (self.position - 1) % self.steps_per_rev

    def cleanup(self):
        GPIO.output(self.step_pin, GPIO.HIGH)
        GPIO.output(self.sleep_pin, GPIO.HIGH)
        GPIO.cleanup([self.step_pin, self.dir_pin])
        log("INFO", "STEPPER", "Pins cleaned up")
