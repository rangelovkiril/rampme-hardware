#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Core tools
sudo apt install -y git curl wget nano

# I2C, SPI, GPIO
sudo apt install -y i2c-tools python3-smbus python3-dev \
  libgpiod2 python3-libgpiod python3-rpi.gpio

# Camera support
sudo apt install -y python3-picamera2 libcamera-apps \
  imx500-all

# Python package management
sudo apt install -y python3-pip python3-venv

# MQTT broker
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Enable I2C and SPI without going into raspi-config
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_camera 0

# Add user to relevant groups
sudo usermod -aG i2c,spi,gpio,video $USER

sudo reboot
