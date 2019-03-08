#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Raspberry Pi simple GPIO loop with no data logging.
    Run a sequence of events after an input trigger is detected.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 08/03/2019
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

PL1 = 0.2 # solenoid pulse length
DT  = 3.0 # delay from solenoid rising edge to TTL out2

trigger_pin   = 16
output_pins   = [25    , 12   , 13   , 22      , 21      ]
output_name   = ["Sol1","TTL1","TTL2","Grn LED","Yel LED"]
output_delays = [0     , 0    , DT   , 2e-3    , 2e-3    ]
output_plen   = [PL1   , 5e-2 , 5e-2 , DT      , DT*2    ]
output_invert = [0     , 0    , 0    , 0       , 1       ] 
debounce_delay = 1.0 # min. time between triggers allowed

# Make a list of events to do when triggered
timings = np.hstack((np.array(output_delays),np.array(output_delays)+np.array(output_plen)))
p = np.hstack((output_pins,output_pins))
i = np.hstack((range(len(output_pins)),range(len(output_pins))))
a = np.hstack((1-np.array(output_invert),output_invert))

event_pins = p[np.argsort(timings)]
event_action = a[np.argsort(timings)]
delays = np.diff(timings[np.argsort(timings)])
delays = np.hstack((delays,0))

print "Event sequence:"
for i in range(len(event_pins)):
    pin_name = output_name[output_pins.index(event_pins[i])]
    print "Pin %i (%s) = %i, then wait %f s" % (event_pins[i], pin_name, event_action[i], delays[i])
print "Then wait for next trigger.\n"


GPIO.setmode(GPIO.BCM)
GPIO.setup(trigger_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for pin, val in zip(output_pins, output_invert):
	GPIO.setup(pin, GPIO.OUT)
	GPIO.output(pin, val)

print("Press CTRL+C to exit")
try:
    t0=time.time()-debounce_delay
    print("Waiting for trigger")
    while 1:
        # trigger when input pin goes LOW (it's an inverted pullup input) and debounce delay passed
        if (GPIO.input(trigger_pin)==0) and (time.time()-t0 > debounce_delay):
            t0=time.time()
            for pin, action, dt in zip(event_pins, event_action, delays):
                GPIO.output(pin, action)
                if dt>0: time.sleep(dt)
            

except KeyboardInterrupt:
    GPIO.cleanup()

print("Done")
