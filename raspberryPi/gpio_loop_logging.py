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
    @date 27/02/2019
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
import os,time,datetime
import h5py
import numpy as np

# Define log file
logfilename='/home/pi/logfile_%s.hdf5' %  datetime.datetime.now().strftime('%d-%m-%y_%Hh%Mm%Ss')

# Report progress and logged variables to terminal?
verbose=True

# GPIO pins and timings for the control/triggering loop.
PL1  = 0.5 # solenoid pulse length
DT0  = 0.5 # delay from TTL out1 to solenoid rising edge
DT1  = 2.0 # delay from solenoid rising edge to TTL out2

trigger_pin   = 16
output_pins   = [25    , 12   , 13   , 22      , 21      ]
output_name   = ["Sol1","TTL1","TTL2","TRG LED","ARM LED"]
output_delays = [DT0   , 0    , DT1  , 1e-3    , 6e-2    ]
output_plen   = [PL1   , 5e-2 , 5e-2 , DT1     , DT1     ]
output_invert = [0     , 0    , 0    , 0       , 1       ] 
debounce_delay = 1.0 # min. time between triggers allowed
busy_indicator_pin = 21 # this pin will be low while the logger is working, ie for a "busy" status LED.
busy_indicator_inv = 1   # is the busy indicator high or low while working

# Device setup special initialization settings
special_args={'debugMode':False, 'init_tc08_config':['K','K','K','T','T','T','X','X'], 'quiet':True,\
             'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}




#####################################################################################################################
# Detect USB devices for datalogging.
usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)

# Detect I2C devices for datalogging.
i2CDevicesFound = i2cDevice.scan_for_devices()
if len(i2CDevicesFound)>0: devices.extend(i2cDevice.load_i2c_devices(i2CDevicesFound, **special_args)) 

# Store the delay settings above into the logfile for posterity.
if os.path.isfile(logfilename): raise IOError("Log file already exists!")
print "Saving to %s" % logfilename
with h5py.File(logfilename,'w') as F: # force new file.
    D=F.create_group('GPIO Timing Loop')
    for v in ['trigger_pin','debounce_delay','busy_indicator_inv','busy_indicator_pin']:
        D.attrs[v]=eval(v)
    for a in ['output_pins','output_name','output_delays','output_plen','output_invert']:
        D.create_dataset(a,data=eval(a))

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
GPIO.output(busy_indicator_pin, busy_indicator_inv)


#####################################################################################################################
# Start loop
print("Press CTRL+C to exit")
try:
    t0=time.time()-debounce_delay
    loop_counter=0
    print("Loop counter = %i\nWaiting for trigger" % loop_counter)
    while 1:
    
        # trigger when input pin goes LOW (it's an inverted pullup input) and debounce delay passed
        if (GPIO.input(trigger_pin)==0) and (time.time()-t0 > debounce_delay):
                
            # Reset clock
            t0=time.time()
            
            # Do GPIO actions first to minimise latency
            for pin, action, dt in zip(event_pins, event_action, delays):
                GPIO.output(pin, action)
                if dt>0: time.sleep(dt)
            
            # Activate 'busy' indicator as we are now going into our datalogging routine,
            # which may take several seconds
            GPIO.output(busy_indicator_pin, 1-busy_indicator_inv)

            # Now update all the logging devices
            for d in devices:
                d.query()

            # Now everything else is done, save to log file and output any other information.
            for d in devices:
                d.log(logfilename)
                if verbose:
                    print d.name
                    d.pprint()
                    #print ''
                
            # Turn off the 'busy' indicator
            GPIO.output(busy_indicator_pin, busy_indicator_inv)
            
            # Tell the user in the terminal that we are ready for the next trigger.
            if verbose:
                print('='*40)
                print("Loop counter = %i\nWaiting for trigger" % loop_counter)

        loop_counter+=1
        #break

except KeyboardInterrupt:
    GPIO.cleanup()

print("Done")
