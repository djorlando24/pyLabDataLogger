#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    TE Connectivity M32JM I2C Pressure Transducer

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
import datetime, time, struct
import numpy as np
from termcolor import cprint

try:
    import smbus
except ImportError:
    cprint("Please install smbus module.",'red')

########################################################################################################################
class m32jmDevice(i2cDevice):

    """ Class providing support for TE Connectivity M3200 series I2C pressure transducer.
        Tested specifically with the M32JM series.
        see:
            https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FM3200%7FA9%7Fpdf%7FEnglish%7FENG_DS_M3200_A9.pdf%7FCAT-PTT0068
            https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Specification+Or+Standard%7FInterfacing_to_DigitalPressure_Modules%7FA3%7Fpdf%7FEnglish%7FENG_SS_Interfacing_to_DigitalPressure_Modules_A3.pdf%7FCAT-PTT0016
        Specify I2C bus and address on initialisation.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        if not self.bridge: assert self.params['bus']
        else: assert self.bridgeDev
        if 'name' in self.params: self.name = self.params['name']+' %s:%s' % (self.params['bus'],hex(self.params['address']))
        if not 'driver' in self.params.keys(): self.params['driver']=None

        self.params['n_channels']=3
        if not 'channel_names' in self.config:
            self.config['channel_names']=['Pressure','Temperature','Status']

        if not 'P_MIN' in self.params: self.params['P_MIN']= 0.
        if not 'P_MAX' in self.params: self.params['P_MAX']= 100.
        if not 'T_MIN' in self.params: self.params['T_MIN']= 0.
        if not 'T_MAX' in self.params: self.params['T_MAX']= 55.
        if not 'P_MIN_COUNTS' in self.params: self.params['P_MIN_COUNTS']=1000
        if not 'P_MAX_COUNTS' in self.params: self.params['P_MAX_COUNTS']=15000
        if not 'T_MIN_COUNTS' in self.params: self.params['T_MIN_COUNTS']=512
        if not 'T_MAX_COUNTS' in self.params: self.params['T_MAX_COUNTS']=1075

        self.params['raw_units']=['PSIG','degC','']
        self.config['eng_units']=['PSIG','degC','']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = 'TE M3200 Series pressure transducer I2C %i:%s' % (self.params['bus'],self.params['address'])

         
        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):

        if self.bridge:
            self.bridgeDev.start(self.params['address'],1)
            time.sleep(0.3)
            data=self.bridgeDev.read(4)
            self.bridgeDev.stop()
        else:
            bus=smbus.SMBus(self.params['bus'])
            bus.write_byte(self.params['address'],self.params['address'])
            data = bus.read_i2c_block_data(self.params['address'],0,4)

        pRaw = (data[0]<<8) | data[1]
        tRaw = (data[2]<<8) | data[3]
        status=pRaw>>14
        pRaw = pRaw & 0x3fff
        tRaw = tRaw >> 5

        scaleOutput = lambda x,loOut,hiOut,loIn,hiIn:  ((x-loIn)/(hiIn-loIn))*(hiOut-loOut) + loOut
        pVal = scaleOutput(pRaw,self.params['P_MIN'], self.params['P_MAX'], self.params['P_MIN_COUNTS'], self.params['P_MAX_COUNTS'])
        tVal = scaleOutput(tRaw,self.params['T_MIN'], self.params['T_MAX'], self.params['T_MIN_COUNTS'], self.params['T_MAX_COUNTS'])
        self.lastValue = [pVal, tVal, status]
        #print(hex(pRaw),hex(tRaw),pVal,tVal)

        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        if self.bridge: 
            self.bridgeDev.stop()
            del self.bridgeDev
        pass
