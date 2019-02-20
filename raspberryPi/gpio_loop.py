#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Raspberry Pi simple GPIO loop with no data logging.
    Run a sequence of events after an input trigger is detected.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 20/10/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""
import RPi.GPIO as GPIO
import time
import numpy as np

# Here are the GPIO pins for my particular setup
# (yours may vary)
# output driving solenoid 1 = pin 25
# output driving solenoid 2 = pin 24
# leds = pins = [22,23,21]
# input buttons = butPins = [16,17,18]
# TTL inputs = [5,6]
# TTL outputs = [12,13]

PL1 = 0.5 # solenoid pulse length
DT  = 1.5 # delay to TTL out2

trigger_pin   = 16
output_pins   = [25 , 12  , 13  , 22, 23, 21]
output_delays = [0  , 1e-3, DT  , 0 , DT, 0 ]
output_plen   = [PL1, 1e-3, 1e-3, DT, DT, DT]
output_invert = [0  ,  0  , 0   , 0 , 0 , 0 ] 
debounce_delay = 0.2 # min. time between triggers allowed

# Make a list of events to do when triggered
timings = np.hstack((np.array(output_delays),np.array(output_delays)+np.array(output_plen)))
p = np.hstack((output_pins,output_pins))
i = np.hstack((range(len(output_pins)),range(len(output_pins))))
a = np.hstack((1-np.array(output_invert),output_invert))

event_pins = p[np.argsort(timings)]
event_action = a[np.argsort(timings)]
delays = np.diff(timings[np.argsort(timings)])

print event_pins
print event_action
print delays

GPIO.setmode(GPIO.BCM)
GPIO.setup(trigger_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for pin, val in zip(output_pins, output_invert):
	GPIO.setup(pin, GPIO.OUT)
	GPIO.output(pin, val)

print("Press CTRL+C to exit")
try:
    t0=time.time()-debounce_delay
    while 1:
        if ~GPIO.input(trigger_pin) and (time.time()-t0 > debounce_delay):
            t0=time.time()
            for pin, action, dt in zip(event_pins, event_action, delays):
                GPIO.output(pin, action)
                if dt>0: time.sleep(dt)
            

except KeyboardInterrupt:
    GPIO.cleanup()

print("Done")
