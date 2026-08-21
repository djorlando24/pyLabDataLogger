#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    MPX5700 Pressure Sensor

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 21/02/2026

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
import datetime, time, struct
import numpy as np
from termcolor import cprint

try:
    import smbus
except ImportError:
    cprint("Please install smbus module.",'red')

########################################################################################################################
class mpx5700Device(i2cDevice):

    """ Class providing support for mpx5700 I2C pressure transducer.
        For ex, DFRobot SEN0456 board.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        if not self.bridge: assert self.params['bus']
        else: assert self.bridgeDev
        if 'name' in self.params: self.name = self.params['name']+' 0x%s' % (hex(self.params['address']))
        if not 'driver' in self.params.keys(): self.params['driver']=None

        self.params['n_channels']=1
        if not 'channel_names' in self.config:
            self.config['channel_names']=['Pressure','Temperature','Status']

        self.params['raw_units']=['Pa abs']
        self.config['eng_units']=['kPa abs']
        self.config['scale']=[0.001]
        self.config['offset']=[0.]
        
        
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = 'MPX5700 pressure transducer I2C 0x%s' % (self.params['address'])
        
        self.config['mean_sample_size']=5
        self.config['use_internal_calibration']=1
        
        
        if self.bridge:
            self.bridgeDev.setspeed(400) #kHz bus speed
            self.bridgeDev.regwr(self.params['address'], 0x05, [self.config['mean_sample_size']]) # Samples per reading
            self.bridgeDev.regwr(self.params['address'], 0x09, [self.config['use_internal_calibration']]) # calibrated mode
        else:
            raise RuntimeError("SMBus not implemented for this sensor")
        
        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):

        if self.bridge:
            buf = self.bridgeDev.regrd(self.params['address'], 0x06, 2)
            self.lastValue = [ ((buf[0] << 8) | buf[1])*10 ]
        else:
            raise RuntimeError("SMBus not implemented for this sensor")

        

        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        if self.bridge: 
            self.bridgeDev.stop()
            del self.bridgeDev
        pass
    
    
    def calibrate(self,actual_pressure_pa=101300):
        '''
        Set zero offset
        '''
    
        Pressure = [0]*2
        ifcalibration = [0]*1
        ifcalibration[0]=1
        plus_or_minus_calibration = [0]*1
    
        self.query()
        values = int(self.lastValue[0])
    
        if(actual_pressure_pa>values):
            plus_or_minus_calibration[0] = 0 #Plus calibration
        else:
            plus_or_minus_calibration[0] = 1 #Minus calibration  
    
        if self.bridge:
            buf = self.bridgeDev.regwr(self.params['address'], 0x0C, plus_or_minus_calibration)
            Pressure_100 = (abs(actual_pressure_pa - values) / 10) #deltaP in hundredths of kPa
            Pressure[0] = (int(Pressure_100) >> 8) & 0xff
            Pressure[1] = int(Pressure_100) & 0xff
            self.bridgeDev.regwr(self.params['address'], 0x0A, Pressure)
            time.sleep(1)
            self.bridgeDev.regwr(self.params['address'], 0x08, ifcalibration)
            
        else:
            raise RuntimeError("SMBus not implemented for this sensor")
        
        
        
