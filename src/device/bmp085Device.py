"""
    Adafruit BMP085 Barometric Pressure Sensor device class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 06/02/2019
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from i2cDevice import *
from device import pyLabDataLoggerIOError
import datetime, time
import numpy as np

try:
    from Adafruit_BMP085 import BMP085
except ImportError:
    print "Error, could not load Adafruit_BMP085 library"

########################################################################################################################
class bmp085Device(bmp085Device):
    """ Class providing support for Adafruit's BMP085 MEMS pressure sensor breakout boards.
        Specify I2C bus and address on initialisation.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        self.params['driver']='BMP085'

        self.params['n_channels']=3
        if not 'channel_names' in self.config:
            self.config['channel_names']=['Temperature','Pressure']

        self.params['raw_units']=['degC','Pa']
        self.config['eng_units']=
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if 'gain' in self.params: self.config['gain']=self.params['gain']
        print "Activating %s on i2c bus at %i:%s with %i channels" % (self.params['driver'],self.params['bus'],self.params['address'],self.params['n_channels'])
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = '%s I2C %i:%s' % (self.params['driver'],self.params['bus'],self.params['address'])

        # Default operating mode
        if not 'mode' in self.params: self.params['mode'] = 3 # ULTRAHIRES mode

        """
            Valid modes:
            0 = ULTRALOWPOWER Mode
            1 = STANDARD Mode
            2 = HIRES Mode
            3 = ULTRAHIRES Mode
        """

        # Initialise the BMP085
        self.BMP = BMP085(self.params['address'], self.params['mode'])
        self.driverConnected=True
        
        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        assert self.BMP

        self.lastValue = [self.BMP.readTemperature(),\
                          self.BMP.readPressure() ]
        
        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        del self.BMP

