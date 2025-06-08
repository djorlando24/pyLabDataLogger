#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    H3LIS331DL accelerometer driver

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
import datetime, time, sys
import numpy as np
from termcolor import cprint
import smbus

########################################################################################################################
class h3lis331dlDevice(i2cDevice):

    """ Class providing support for H3LIS331DL
        Specify I2C bus and address on initialisation.

        provide ACCL_RANGE (100/200/400g) and ACCL_SAMPLES for software averaging.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        if 'name' in self.params: self.name = self.params['name']+' %i:%s' % (self.params['bus'],hex(self.params['address']))
        if not 'driver' in self.params.keys(): self.params['driver']=None

        self.params['n_channels']=4
        if not 'channel_names' in self.config:
            self.config['channel_names']=['accel_X','accel_Y','accel_Z','magnitude']

        if not 'ACCL_RANGE' in self.params: self.params['ACCL_RANGE']=100. # 100 g default
        if not 'ACCL_SAMPLES' in self.params: self.params['ACCL_SAMPLES']=10. # at 50 Hz, sample for 0.2s

        self.params['ACCL_SCALING']=(2**15)/self.params['ACCL_RANGE'] # 16 bit signed output, so value is -2^15 to +2^15 in range.
        self.params['raw_units']=['g','g','g','g']
        self.config['eng_units']=['g','g','g','g']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = 'H3LIS331DL Accelerometer I2C %i:%s' % (self.params['bus'],self.params['address'])

        self.bus = smbus.SMBus(self.params['bus'])

        # Select control register 1, 0x20(32)
        #       0x27(39)    Power ON mode, Data output rate = 50 Hz
        #                   X, Y, Z-Axis enabled
        self.bus.write_byte_data(self.params['address'], 0x20, 0x27)

        # Select control register 4, 0x23(35)
        #       0x00(00)    Continuous update, Full scale selection = +/-100g
        if self.params['ACCL_RANGE']==100.:
            self.bus.write_byte_data(self.params['address'], 0x23, 0x00)
        elif self.params['ACCL_RANGE']==200.:
            self.bus.write_byte_data(self.params['address'], 0x23, 0x01)
        elif self.params['ACCL_RANGE']==400.:
            self.bus.write_byte_data(self.params['address'], 0x23, 0x02)
        else:
            raise ValueError("Bad ACCL_RANGE for H3LIS331DL: acceptable values are 100g, 200g, 400g.")

        time.sleep(0.01)

        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        
        val=[0,0,0]
        for n in range(int(self.params['ACCL_SAMPLES'])):
            x=0
            for offset in [(0x28,0x29),(0x2a,0x2b),(0x2c,0x2d)]:
                data0 = self.bus.read_byte_data(self.params['address'], offset[0])
                data1 = self.bus.read_byte_data(self.params['address'], offset[1])

                # Convert the data
                accl = data1 * 256 + data0
                if accl > 32767 :
                    accl -= 65536
                
                val[x] += accl
                x+=1
            time.sleep(0.021) # 50 Hz refresh, so go a very little bit slower than this.

        self.lastValue = [a/float(self.params['ACCL_SAMPLES'])/float(self.params['ACCL_SCALING']) for a in val]
        self.lastValue.append(np.sum(np.array(self.lastValue)**2)**0.5) # geometric sum of XYZ

        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        del self.bus
        pass
