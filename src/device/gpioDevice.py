"""
    GPIO device class - for Raspberry Pi
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 28/11/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from device import device
import datetime, time
import numpy as np

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
except ImportError:
    print "Error, RPi.GPIO could not be loaded"
    exit()
    
########################################################################################################################
class gpioDevice(device):
    """ Class providing support for Raspberry Pi GPIO """

    def __init__(self,params={},**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "Raspberry Pi GPIO"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        if params is {}: return
        
        # Set up default input pins for Raspberry Pi controller. (just inputs, not outputs).
        if not 'pins' in self.params: raise KeyError("Please  specify which input pins to monitor")
        if not 'pup' in self.params:
                print "Pull-up/down not specified: setting default mode pull-up off"
                self.params['pup']=(False)*len(self.params['pins'])
        elif len(self.params['pup']) < len(self.params['pins']):
                raise IndexError("number of pup entries does not match number of pins")
        if not 'channel_names' in self.params:
                self.params['channel_names']=['Pin%02i' % p for p in self.params['pins']]
        self.params['n_channels']=len(self.params['pins'])
        self.config['scale']=np.ones(len(self.params['pins']),)
        self.config['offset']=np.zeros(len(self.params['pins']),)
        self.params['raw_units']=['']*len(self.params['pins'])
        self.config['eng_units']=['']*len(self.params['pins'])
        
        self.scan()
        return

    # Detect if device is present
    def scan(self,override_params=None):
        if override_params is not None: self.params = override_params
        assert(GPIO)
        self.activate()

    # Activate I/O
    def activate(self):
        if len(self.params['pins']) < 1:
            print "Error, no input GPIO pins specified"
            return
        for pin, pup in zip(self.params['pins'], self.params['pup']):
            if pup: GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            else: GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.driverConnected=True
        
        self.query()

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        self.lastValue = []
        for pin in self.params['pins']:
            self.lastValue.append(GPIO.input(pin))
        
        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
        
        self.updateTimestamp()
        return
        
    # Deactivate connection to device (close serial port)
    def deactivate(self):
        GPIO.cleanup()
        self.driverConnected=False
        return

if __name__ == '__main__':
    D=gpioDevice()
    while True:
        time.sleep(1)
        print D.query()
