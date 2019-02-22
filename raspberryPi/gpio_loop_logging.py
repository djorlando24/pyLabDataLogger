#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Raspberry Pi simple GPIO loop with HDF5 data logging of connected USB and I2C devices.
    Run a sequence of events after an input trigger is detected.
    
    This is a simple implementation with a single thread. 
    Logging is done after the GPIO loop is complete each time.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 22/10/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

import RPi.GPIO as GPIO
from pyLabDataLogger.device import usbDevice, i2cDevice
import time,datetime
import numpy as np

# Define log file
logfilename='logfile_%s.hdf5' %  datetime.datetime.now().strftime('%d-%m-%y_%Hh%Mm%Ss')
print "Saving to %s" % logfilename

# GPIO pins and timings for the control/triggering loop.
PL1 = 0.5 # solenoid pulse length
DT  = 1.5 # delay from solenoid rising edge to TTL out2

trigger_pin   = 16
output_pins   = [25    , 12   , 13   , 22      , 21      ]
output_name   = ["Sol1","TTL1","TTL2","Grn LED","Yel LED"]
output_delays = [0     , 0    , DT   , 2e-3    , 2e-3    ]
output_plen   = [PL1   , 5e-2 , 5e-2 , DT      , DT      ]
output_invert = [0     , 0    , 0    , 0       , 1       ] 
debounce_delay = 1.0 # min. time between triggers allowed
busy_indicator_pin = 22 # this pin will be high while the logger is working, ie for a "busy" status LED.

# Device setup special initialization settings
special_args={'debugMode':False, 'init_tc08_config':['K','K','K','T','T','T','X','X'], 'quiet':True,\
             'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}




#####################################################################################################################
# Detect USB devices.
usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)

# Detect I2C devices
i2CDevicesFound = i2cDevice.scan_for_devices()
if len(i2CDevicesFound)>0: devices.extend(i2cDevice.load_i2c_devices(i2CDevicesFound, **special_args)) 

#####################################################################################################################
# GPIO timing loop setup:
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


# Start GPIO configuration
GPIO.setmode(GPIO.BCM)
GPIO.setup(trigger_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for pin, val in zip(output_pins, output_invert):
	GPIO.setup(pin, GPIO.OUT)
	GPIO.output(pin, val)
GPIO.setup(busy_indicator_pin, GPIO.OUT)
GPIO.output(busy_indicator_pin, 0)


#####################################################################################################################
# Start loop
print("Press CTRL+C to exit")
try:
    t0=time.time()-debounce_delay
    print("Waiting for trigger")
    while 1:
        # trigger when input pin goes LOW (it's an inverted pullup input) and debounce delay passed
        if (GPIO.input(trigger_pin)==0) and (time.time()-t0 > debounce_delay):
                
            # Reset clock
            t0=time.time()
            
            # Do GPIO actions first to minimise latency
            for pin, action, dt in zip(event_pins, event_action, delays):
                GPIO.output(pin, action)
                if dt>0: time.sleep(dt)

            # Now update all the logging devices
            GPIO.output(busy_indicator_pin, 1)
            for d in devices:
                d.query()

            # Now everything else is done, save to log file and output any other information.
            for d in devices:
                d.log(logfilename)
                print d.name
                d.pprint()
                print ''
            GPIO.output(busy_indicator_pin, 0)

except KeyboardInterrupt:
    GPIO.cleanup()

print("Done")
