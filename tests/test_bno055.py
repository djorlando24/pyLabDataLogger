#!/usr/bin/env python3
import serial,sys
import time
import adafruit_bno055
time.sleep(.1)
print("Open serial port")
uart = serial.Serial("/dev/ttyUSB0")
time.sleep(.1)
print("Initialise device")
sensor=None
while sensor is None:
    try:
        sensor = adafruit_bno055.BNO055_UART(uart)
    except OSError:
        time.sleep(1)
        print(".")
time.sleep(.1)
print("Get value")
vars = [x for x in dir(sensor) if x[0]!='_']
for v in vars:
    try:
        print(v,':', getattr(sensor,v))
    except:
        print(v, ': fail')
    time.sleep(.1)
print("Closing device")
del sensor
uart.close()
