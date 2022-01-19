"""
    GPIO device class - for Raspberry Pi
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2
    @date 19/01/2022
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from .device import device
from .device import pyLabDataLoggerIOError
import datetime, time
import numpy as np
from termcolor import cprint

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
except ImportError:
    cprint( "Error, RPi.GPIO could not be loaded", 'red', attrs=['bold'])
    exit()
    
########################################################################################################################
class gpioDevice(device):
    """ Class providing support for Raspberry Pi GPIO """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "Raspberry Pi GPIO"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        if params is {}: return
        
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet
        
        # Set up default input pins for Raspberry Pi controller. (just inputs, not outputs).
        if not 'pins' in self.params: raise KeyError("Please  specify which input pins to monitor")
        if not 'pup' in self.params:
                cprint( "Pull-up/down not specified: setting default mode pull-up off" , 'yellow')
                self.params['pup']=(False)*len(self.params['pins'])
        elif len(self.params['pup']) < len(self.params['pins']):
                raise IndexError("number of pup entries does not match number of pins")
        if 'channel_names' in self.params: self.config['channel_names']=self.params['channel_names']
        elif 'channel_names' in kwargs: self.config['channel_names']=kwargs['channel_names']
        else: self.params['channel_names']=['Pin%02i' % p for p in self.params['pins']]
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
            cprint( "Error, no input GPIO pins specified", 'red', attrs=['bold'])
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

# A little test script.
if __name__ == '__main__':
    D=gpioDevice()
    while True:
        time.sleep(1)
        print(D.query())
