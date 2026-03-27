# 🦽 RampMe Hardware

> Embedded hardware system for **RampMe** — an automatic wheelchair ramp for public transport in Sofia.  
> Built for **Hack TUES 12** · Theme: *Code to Care* · Subtheme: *LimitLess*

---

## 📖 What It Does

A wheelchair user opens the RampMe PWA, selects their bus, stop, and arrival time. The system tracks the bus in real time using data from **Център за градска мобилност**. When the bus approaches the stop, an MQTT message is sent to the Raspberry Pi unit installed on that bus. The driver presses the green button to confirm deployment. The ramp extends via a lead screw driven by a stepper motor, with a buzzer providing audible feedback throughout. The driver can also manually control the ramp at any time using the two physical buttons. A hardware emergency stop button cuts power to the motor directly, bypassing the MCU entirely.

---

## 🔧 Hardware

| Component | Part | Purpose |
|---|---|---|
| Compute | Raspberry Pi 4 | Edge controller, MQTT client |
| Motor | Stepper motor + DM542 driver | Drives the lead screw to extend/retract the ramp |
| Lead screw | Винтова предавка | Converts motor rotation to linear ramp movement |
| Distance | LiDAR | Checks door clearance before deployment |
| Buzzer | PK-12N40PE-TQ + 2N2222A + 1kΩ | Audible alert while ramp is moving |
| Deploy button | F24S1-1243GFS002 (green) | Driver initiates ramp deployment |
| Retract button | F24S1-1243GFS002 (red) | Driver initiates ramp retraction |
| Emergency stop | Normally closed button | Cuts 12V to DM542 driver directly — hardware level, MCU independent |

---

## 📌 GPIO Pin Assignments

| Pin | Component | Role |
|---|---|---|
| GPIO 17 | Buzzer | Signal via 2N2222A transistor |
| GPIO 23 | Stepper driver ENA+ | Enable (common anode, active LOW) |
| GPIO 24 | Stepper driver PUL+ | Step pulse (common anode) |
| GPIO 25 | Stepper driver DIR+ | Direction |
| GPIO 16 | Green button | Deploy — NO contact |
| GPIO 12 | Red button | Retract — NO contact |

> I2C devices (TFMINI-S) share **SDA (GPIO 2)** and **SCL (GPIO 3)**.

---

## 🛑 Emergency Stop

The emergency stop is a **normally closed (NC) button wired in series between the Enable input on the DM542 driver and the RPI**. Pressing it physically breaks the power circuit to the driver, stopping the motor instantly regardless of what the software is doing. This is the industry standard approach for emergency stops in motor control systems — no firmware can override it.

---

## 🔌 Wiring Diagrams

### Stepper Motor + DM542 Driver
![Stepper wiring](docs/stepper_motor.png)

### Buzzer + 2N2222A Transistor
![Buzzer wiring](docs/buzzer.png)

### Green Deploy Button
![Deploy button wiring](docs/push-button-1.png)

### Red Retract Button
![Retract button wiring](docs/push-button-2.png)

### Emergency Stop
![Emergency stop wiring](docs/button_estop_wiring.png)

### LiDAR
![LiDAR wiring](docs/lidar.png)

---

## 🗂 Software Structure

```
drivers/
  stepper_motor.py   # stepper motor driver wrapper
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
setup.sh             # One-shot setup script for fresh Pi OS installs
```

---

## ⚙️ Setup

Flash **Raspberry Pi OS Lite 64-bit (Bookworm)** onto an SD card, then SSH in and run:

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Install all Python dependencies and system packages
- Enable I2C, SPI, and camera interfaces
- Install and start Mosquitto MQTT broker
- Enable avahi-daemon for mDNS (`pi-ht.local`)
- Reboot when complete

Then clone the repo:

```bash
git clone git@github.com:rangelovkiril/rampme-hardware.git
```

> ⚠️ `setup.sh` is not yet in the repo — add it before running on a fresh device.

---

## 📡 MQTT Topics

| Topic | Direction | Purpose |
|---|---|---|
| `ramp/{bus_id}/deploy` | PWA → Pi | Trigger ramp deployment |
| `ramp/{bus_id}/retract` | PWA → Pi | Trigger ramp retraction |
| `ramp/{bus_id}/status` | Pi → PWA | Current ramp state |
| `ramp/{bus_id}/emergency` | Pi → PWA | Emergency stop triggered |
| `ramp/{bus_id}/sensors` | Pi → PWA | Sensor readings |

---

## ⚠️ Important Wiring Notes

- The DM542 uses **common anode** wiring — PUL+, DIR+, ENA+ connect to 5V, and the GPIO pins drive the negative terminals. Logic is inverted from standard drivers.
- The buzzer runs on 5V from the step-down converter. GPIO 17 drives the base of a 2N2222A transistor through a 1kΩ resistor — **never connect the buzzer directly to a GPIO pin**.
- Button LEDs connect to 5V via a ~220Ω resistor — **do not connect directly to a GPIO pin**.
- The emergency stop is wired at the power level, not the GPIO level. Do not attempt to replicate this in software.
- **GPIO 8, 9, 10, 11** are reserved for SPI. **GPIO 2, 3** are reserved for I2C. Do not use these for buttons or other digital I/O.

---

## 🛠 Built With

- Python 3 + RPi.GPIO
- Mosquitto MQTT broker
- Next.js PWA → [rampme-software](https://github.com/rangelovkiril/rampme-software)

---

*Hack TUES 12 · Code to Care · LimitLess*
