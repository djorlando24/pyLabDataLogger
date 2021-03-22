"""
    Adafruit BMP Barometric Pressure Sensor device class
    Compatible with BMP085 and BMP150 
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.2
    @date 22/03/2021
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

from .i2cDevice import *
from .device import pyLabDataLoggerIOError
import datetime, time
import numpy as np
from termcolor import cprint

try:
    import Adafruit_BMP.BMP085 as BMP085
except ImportError:
    cprint( "Error, could not load Adafruit_BMP085 library", 'red', attrs=['bold'])

########################################################################################################################
class bmpDevice(i2cDevice):
    """ Class providing support for Adafruit's BMP MEMS pressure sensor breakout boards.
    Works with BMP085 and BMP150.
        Specify I2C bus and address on initialisation.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        assert BMP085
        self.params['driver']='BMP'

        self.params['n_channels']=2
        if not 'channel_names' in self.config:
            self.config['channel_names']=['Temperature','Pressure']

        self.params['raw_units']=['degC','Pa']
        self.config['eng_units']=['degC','Pa']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if 'gain' in self.params: self.config['gain']=self.params['gain']
        cprint( "Activating %s on i2c bus at %i:%s with %i channels" % (self.params['driver'],self.params['bus'],self.params['address'],self.params['n_channels']), 'green')
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
        self.BMP = BMP085.BMP085(mode=self.params['mode'],\
                                 address=int(self.params['address'],16),\
                                 busnum=self.params['bus'])
        self.driverConnected=True
        
        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        assert self.BMP

        self.lastValue = [self.BMP.read_temperature(),\
                          self.BMP.read_pressure() ]
        
        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        del self.BMP

