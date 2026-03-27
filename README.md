# RampMe Hardware

Embedded hardware system for **RampMe** — an automatic wheelchair ramp for public transport in Sofia. Built for Hack TUES 12 under the theme *Code to Care*, subtheme *LimitLess*.

## What It Does

A wheelchair user opens the RampMe PWA, selects their bus, stop, and arrival time. The system tracks the bus in real time using data from Център за градска мобилност. When the bus approaches the stop, an MQTT message is sent to the Raspberry Pi unit installed on that bus. The driver presses the green button to confirm deployment. The ramp extends via a lead screw driven by a stepper motor, with a buzzer providing audible feedback throughout. The driver can also manually control the ramp at any time using the two physical buttons. A hardware emergency stop button cuts power to the motor directly, bypassing the MCU entirely.

## Hardware

| Component | Part | Purpose |
|---|---|---|
| Compute | Raspberry Pi 4 | Edge controller, MQTT client |
| Motor | Stepper motor + DM542 driver | Drives the lead screw to extend/retract the ramp |
| Lead screw | Винтова предавка | Converts motor rotation to linear ramp movement |
| Thermal camera | Grove MLX90640 110° | Detects human presence on ramp before retraction |
| Environmental | Grove BME680 | Temperature, humidity, pressure, VOC monitoring |
| Distance | LiDAR | Checks door clearance before deployment |
| Colour | TCS34725 | RGB colour sensing |
| Buzzer | PK-12N40PE-TQ + 2N2222A + 1kΩ | Audible alert while ramp is moving |
| Deploy button | F24S1-1243GFS002 (green) | Driver initiates ramp deployment |
| Retract button | F24S1-1243GFS002 (red) | Driver initiates ramp retraction |
| Emergency stop | Normally closed button | Cuts 12V to DM542 driver directly — hardware level, MCU independent |

## GPIO Pin Assignments

| Pin | Component | Role |
|---|---|---|
| GPIO 17 | Buzzer | Signal via 2N2222A transistor |
| GPIO 23 | Stepper ENA- | Enable (common anode, active LOW) |
| GPIO 24 | Stepper PUL- | Step pulse (common anode) |
| GPIO 25 | Stepper DIR- | Direction |
| GPIO 16 | Green button | Deploy — NO contact |
| GPIO 12 | Red button | Retract — NO contact |

I2C devices (BME680, MLX90640, TCS34725) share SDA (GPIO 2) and SCL (GPIO 3).

## Emergency Stop

The emergency stop is a **normally closed (NC) button wired in series between the 12V supply and the DM542 driver**. Pressing it physically breaks the power circuit to the driver, stopping the motor instantly regardless of what the software is doing. This is the industry standard approach for emergency stops in motor control systems — no firmware can override it.

## Wiring Diagrams

| Diagram | File |
|---|---|
| Stepper motor + DM542 driver | [docs/stepper_wiring.png](docs/stepper_wiring.png) |
| Buzzer + 2N2222A transistor | [docs/buzzer_wiring.png](docs/buzzer_wiring.png) |
| Green deploy button | [docs/button_deploy_wiring.png](docs/button_deploy_wiring.png) |
| Red retract button | [docs/button_retract_wiring.png](docs/button_retract_wiring.png) |
| Emergency stop | [docs/button_estop_wiring.png](docs/button_estop_wiring.png) |
| LiDAR | [docs/lidar_wiring.png](docs/lidar_wiring.png) |

## Software
```
drivers/
  stepper_motor.py   # DM542 common anode stepper driver
  buzzer.py          # Buzzer with beep patterns
  push_button.py     # GPIO button with callback and polling
  ramp.py            # Ramp controller — buttons + MQTT deploy/retract
tests/
  stepper_test.py
  buzzer_test.py
  push_button_test.py
  ramp_test.py
utils/
  logger.py
```

## Setup

Flash Raspberry Pi OS Lite 64-bit (Bookworm) then run:
```bash
chmod +x setup.sh
./setup.sh
```

This installs all dependencies, enables I2C/SPI/camera, starts Mosquitto, and enables avahi for mDNS (`pi-ht.local`).

Clone the repo after setup:
```bash
git clone git@github.com:rangelovkiril/rampme-hardware.git
```

## MQTT Topics

| Topic | Direction | Purpose |
|---|---|---|
| `ramp/{bus_id}/deploy` | PWA → Pi | Trigger ramp deployment |
| `ramp/{bus_id}/retract` | PWA → Pi | Trigger ramp retraction |
| `ramp/{bus_id}/status` | Pi → PWA | Current ramp state |
| `ramp/{bus_id}/emergency` | Pi → PWA | Emergency stop triggered |
| `ramp/{bus_id}/sensors` | Pi → PWA | Sensor readings |

## Important Wiring Notes

- The DM542 uses **common anode** wiring — PUL+, DIR+, ENA+ connect to 5V, and the GPIO pins drive the negative terminals. Logic is inverted from standard drivers.
- The buzzer runs on 5V from the step-down converter. GPIO 17 drives the base of a 2N2222A transistor through a 1kΩ resistor — never connect the buzzer directly to a GPIO pin.
- Button LEDs connect to 5V via a ~220Ω resistor — do not connect directly to a GPIO pin.
- The emergency stop is wired at the power level, not the GPIO level. Do not attempt to replicate this in software.
- GPIO 8, 9, 10, 11 are reserved for SPI. GPIO 2, 3 are reserved for I2C. Do not use these for buttons or other digital I/O.

## Built With

- Python 3 + RPi.GPIO
- Mosquitto MQTT broker
- Next.js PWA (see [rampme-frontend](https://github.com/rangelovkiril/rampme-frontend))

---

*Hack TUES 12 — Code to Care — LimitLess*
