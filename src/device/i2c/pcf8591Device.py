#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    PCF8591 ADC support

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2023 LTRAC
    @license GPL-3.0+
    @version 1.4.0
    @date 08/06/25

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
    import smbus
except ImportError:
    cprint("Please install smbus module.",'red')


########################################################################################################################
class pcf8591Device(i2cDevice):

    """ Class providing support for PCF8591 8Bit ADC
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
            self.config['channel_names']=['A0','A1','A2','A3']

        if not 'VMIN' in self.params: self.params['VMIN']=0.
        if not 'VMAX' in self.params: self.params['VMAX']=3.3*0.9

        self.params['raw_units']=['V']*4
        self.config['eng_units']=['V']*4
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = 'PCF8591 ADC I2C %i:%s' % (self.params['bus'],self.params['address'])

        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):

        self.lastValue = []
        bus=smbus.SMBus(self.params['bus'])
        for offset in [0x05,0x06,0x03,0x04]:
            bus.write_byte(self.params['address'],offset)
            data = bus.read_byte(self.params['address'])
            self.lastValue.append(data/255.*(self.params['VMAX']-self.params['VMIN']) + self.params['VMIN'])
            #print(hex(offset),data)

        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        pass
