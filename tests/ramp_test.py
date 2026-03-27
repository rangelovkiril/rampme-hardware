from drivers.stepper_motor import StepperMotor
from drivers.buzzer import Buzzer
from drivers.push_button import Button
from drivers.ramp import Ramp

motor = StepperMotor()
buzzer = Buzzer()
deploy_button = Button(pin=16)
retract_button = Button(pin=12)

ramp = Ramp(
    motor=motor,
    deploy_button=deploy_button,
    retract_button=retract_button,
    buzzer=None,
)

try:
    print("Hold green button to deploy, hold red button to retract.")
    print("Ctrl+C to quit.")
    ramp.run()

finally:
    motor.disable()
    motor.cleanup()
    buzzer.cleanup()
    deploy_button.cleanup()
    retract_button.cleanup()