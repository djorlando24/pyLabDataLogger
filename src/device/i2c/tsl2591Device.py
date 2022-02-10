"""
    TSL2591 light sensor support

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2.2
    @date 10/02/2022
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
from ..device import pyLabDataLoggerIOError
import datetime, time
import numpy as np
from termcolor import cprint

try:
    import board, busio
    import adafruit_tsl2591
except ImportError:
    cprint("Please install adafruit-circuitpython-tsl2591 from pip")

########################################################################################################################
class tsl2591Device(i2cDevice):

    """ Class providing support for TSL2591
        Specify I2C bus and address on initialisation.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        if 'name' in self.params: self.name = self.params['name']+' %i:%s' % (self.params['bus'],hex(self.params['address']))
        if not 'driver' in self.params.keys(): self.params['driver']=None

        self.params['n_channels']=4
        if not 'channel_names' in self.config:
            self.config['channel_names']=['Lux','IR','Visible','Full Spectrum']

        self.params['VIS_RANGE']=float(2**32)
        self.params['IR_RANGE'] =float(2**16)
        self.params['raw_units']=['lux','','','']
        self.config['eng_units']=['lux','','','']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = 'TSL2591 Light Sensor I2C %i:%s' % (self.params['bus'],self.params['address'])

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.dev = adafruit_tsl2591.TSL2591(self.i2c)

        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):

        self.lastValue = [ self.dev.lux, self.dev.infrared/self.params['IR_RANGE'], self.dev.visible/self.params['VIS_RANGE'], self.dev.full_spectrum/self.params['VIS_RANGE'] ]
        
        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        del self.dev
        del self.i2c
