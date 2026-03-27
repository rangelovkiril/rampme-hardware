import time
import threading
from drivers.stepper_motor import StepperMotor
from drivers.buzzer import Buzzer
from drivers.push_button import Button
from drivers.mock_door import MockDoor
from drivers.ramp import Ramp

motor = StepperMotor()
buzzer = Buzzer()
deploy_button = Button(pin=16)
retract_button = Button(pin=12)
door = MockDoor()

ramp = Ramp(
    motor=motor,
    deploy_button=deploy_button,
    retract_button=retract_button,
    buzzer=None,
    mock_door=door,
)

try:
    print("=== Test 1: HTTP deploy — put something in front of LiDAR to block ===")
    ramp.deploy()
    time.sleep(0.3)
    while ramp.is_moving:
        time.sleep(0.1)
    print(f"Status: {ramp.get_status()}")
    time.sleep(2)

    print("\n=== Test 2: HTTP deploy — clear the LiDAR ===")
    ramp.deploy()
    time.sleep(0.3)
    while ramp.is_moving:
        time.sleep(0.1)
    print(f"Status: {ramp.get_status()}")
    time.sleep(2)

    print("\n=== Test 3: HTTP retract ===")
    ramp.retract()
    time.sleep(0.3)
    while ramp.is_moving:
        time.sleep(0.1)
    print(f"Status: {ramp.get_status()}")
    time.sleep(2)

    print("\n=== Test 4: Button control — block LiDAR and try deploy button ===")
    print("Hold GREEN to deploy, RED to retract, Ctrl+C to quit.")
    ramp.run()

finally:
    motor.disable()
    motor.cleanup()
    buzzer.cleanup()
    deploy_button.cleanup()
    retract_button.cleanup()
    door.close()