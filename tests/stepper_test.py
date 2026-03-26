import time
from drivers.stepper_motor import StepperMotor

motor = StepperMotor()

print("Enabling motor...")
motor.enable()
time.sleep(0.5)

print("Spinning clockwise 200 steps (1 full revolution)...")
motor.set_direction(clockwise=True)
motor.step(steps=200, delay=0.005)
time.sleep(1)

print("Spinning counter-clockwise 200 steps (1 full revolution back)...")
motor.set_direction(clockwise=False)
motor.step(steps=200, delay=0.005)
time.sleep(1)

print("Spinning clockwise 400 steps (2 full revolutions) slowly...")
motor.set_direction(clockwise=True)
motor.step(steps=400, delay=0.01)
time.sleep(1)

print("Spinning counter-clockwise 400 steps (2 full revolutions) slowly...")
motor.set_direction(clockwise=False)
motor.step(steps=400, delay=0.01)
time.sleep(1)

print(f"Final position: {motor.position}")

print("Disabling motor...")
motor.disable()

print("Cleaning up...")
motor.cleanup()

print("Done.")
