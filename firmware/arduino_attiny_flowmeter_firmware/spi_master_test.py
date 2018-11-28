#!/usr/bin/python

# This program acts as an SPI Master for the ATTINY45
# connected to the Raspberry PI's SPI bus.

# Daniel Duke <daniel.duke@monash.edu>
# Laboratory for Turbulence Research in Aerospace & Combustion 
# Monash University

import RPi.GPIO as gpio
import spidev
import time
import sys

print "Setting up SPI bus..."
spi = spidev.SpiDev()
spi.open(0, 1)  # ATTINY CS is on CE1
spi.max_speed_hz = 7629 # slowest allowed

if len(sys.argv)>1:
	print "Resetting the ATTINY..."
	gpio.setmode(gpio.BCM)
	gpio.setup(20,gpio.OUT)
	gpio.output(20,False)
	time.sleep(0.05)
	gpio.output(20,True)
	time.sleep(1) # wait a bit

print "Listening (press CTRL-C to exit)"
while True:
	buf=[0,0]
	ret= spi.xfer2(buf)
	print [ hex(n) for n in ret ], (buf[0]<<8) +buf[1]
	time.sleep(.5)
