#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    AHT10/AHT20 temperature and humidity sensor support

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 13/06/25

    Multiphase Flow Laboratory
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
    import adafruit_ahtx0
except ImportError:
    cprint("Please install adafruit-circuitpython-ahtx0 via pip",'red')

########################################################################################################################
class ahtx0Device(i2cDevice):

    """ Class providing support for AHT20 Temp & Humidity sensor via I2C
        Specify I2C bus and address on initialisation.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        if 'name' in self.params: self.name = self.params['name']+' I2C 0x%x' % (self.params['address'])
        if not 'driver' in self.params.keys(): self.params['driver']=None

        self.params['n_channels']=2
        if not 'channel_names' in self.config:
            self.config['channel_names']=['Temperature','Humidity']

        self.params['raw_units']=['degC','%RH']
        self.config['eng_units']=['degC','%RH']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = '%s temperature sensor I2C 0x%x' % (self.params['driver'],self.params['address'])

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.dev = adafruit_ahtx0.AHTx0(self.i2c)

        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):

        self.lastValue = [ self.dev.temperature, self.dev.relative_humidity ]
        
        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        del self.dev
        del self.i2c
