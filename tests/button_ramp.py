import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from drivers.stepper_motor import StepperMotor
from drivers.buzzer import Buzzer
from drivers.push_button import Button
from drivers.ramp import Ramp

motor = StepperMotor()
deploy_button = Button(pin=16)
retract_button = Button(pin=12)

ramp = Ramp(
    motor=motor,
    deploy_button=deploy_button,
    retract_button=retract_button,
    buzzer=None,
)

try:
    print("Hold GREEN to extend, hold RED to retract. Ctrl+C to quit.")
    ramp.run()

finally:
    motor.disable()
    motor.cleanup()
    deploy_button.cleanup()
    retract_button.cleanup()