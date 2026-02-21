#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    MPR121 capacitative touch sensor

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
    import adafruit_mpr121
except ImportError:
    cprint("Please install adafruit_mpr121 from https://github.com/adafruit/Adafruit_CircuitPython_MPR121",'red')
    
########################################################################################################################
class mpr121Device(i2cDevice):

    """ Class providing support for MPR121 touch sensor
        Specify I2C bus and address on initialisation.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        if 'name' in self.params: self.name = self.params['name']+' 0x%s' % (hex(self.params['address']))
        if not 'driver' in self.params.keys(): self.params['driver']=None

        if not 'channel_names' in self.config:
            self.config['channel_names']=['Ch%i' % i for i in range(12)]
        self.params['n_channels']=len(self.config['channel_names'])

        self.params['raw_units']=['']*self.params['n_channels']
        self.config['eng_units']=['']*self.params['n_channels']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = 'MPR121 capacitative touch sensor I2C 0x%s' % (self.params['address'])

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.dev=adafruit_mpr121.MPR121(self.i2c)

        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):

        self.lastValue = [ self.dev[i].value for i in range(self.params['n_channels']) ]

        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        del self.dev
        del self.i2c
        pass
