#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Adafruit ADS1x15 Analog to Digital Converter Class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2023 LTRAC
    @license GPL-3.0+
    @version 1.3.0
    @date 23/12/2022
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
    import Adafruit_ADS1x15
except ImportError:
    cprint( "Error, could not load Adafruit_ADS1x15 library", 'red', attrs=['bold'])

########################################################################################################################
class ads1x15Device(i2cDevice):
    """ Class providing support for Adafruit's ADS1x15 breakout boards (ADS1015, ADS1115).
        Specify I2C bus, address and driver (ADS1015/ADS1115) on initialisation.
        Channel gains can be specified with the gain config parameter (a list).
        Setting 'differential' parameter True gives 2 outputs instead of 4. """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        if not 'driver' in self.params.keys(): self.params['driver']='ads1115'
        if 'name' in self.params: self.name = self.params['name']+' %i:%s' % (self.params['bus'],hex(self.params['address']))

        if self.params['driver']=='ADS1115':
            self.ADC =  Adafruit_ADS1x15.ADS1115(address=int(self.params['address'],16), busnum=self.params['bus'])
        elif self.params['driver']=='ADS1015':
            self.ADC =  Adafruit_ADS1x15.ADS1015(address=int(self.params['address'],16), busnum=self.params['bus'])
        else:
            cprint( "Error: unknown driver. Choices are ADS1015 or ADS1115" ,'red',attrs=['bold'] )
            return

        if not 'differential' in self.params.keys(): 
            self.diffDefault=True
            self.diff=True
        else: 
            self.diffDefault=False
            self.diff=self.params['differential']

        if self.diff:
            self.params['n_channels']=2
            if not 'channel_names' in self.config:
                self.config['channel_names']=['ChA','ChB']
        else:
            self.params['n_channels']=4
            if not 'channel_names' in self.config:
                self.config['channel_names']=['Ch1','Ch2','Ch3','Ch4']


        self.params['raw_units']=['V']*self.params['n_channels']
        self.config['eng_units']=['V']*self.params['n_channels']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if 'gain' in self.params: self.config['gain']=self.params['gain']

        cprint( "Activating %s on i2c bus at %i:%s with %i channels" % (self.params['driver'],self.params['bus'],hex(self.params['address']),self.params['n_channels']) , 'green' )
        if self.diffDefault: print("\tDifferential mode (default)")
        elif self.diff: print("\tDifferential mode specified")
        else: print("\tSingle-ended mode")
        
        self.apply_config()
        self.driverConnected=True
        
        return

    # Apply configuration (i.e. gain parameter)
    def apply_config(self,default_gain=2/3):
        valid_gain_values=[2/3, 1,2,4,8,16]
        if not 'gain' in self.config.keys(): self.config['gain']=[default_gain]*self.params['n_channels']
        for chg in self.config['gain']:
            if not chg in valid_gain_values:
                cprint( "Error, gain values are invalid. Resetting", 'yellow' )
                self.config['gain']=[default_gain]*self.params['n_channels']
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        assert self.ADC
        # Read all the ADC channel values in a list.
        values = [0]*4
        for i in range(4):
            if self.diff: j=i/2
            else: j=i
            values[i] = self.ADC.read_adc(i, gain=self.config['gain'][j])*4.096/32768.
            if self.config['gain'][j]==0: values[i] /= 2/3.
            else: values[i] /= self.config['gain'][j]
        self.updateTimestamp()
        
        if self.diff:
            self.lastValue=[values[0]-values[1],values[2]-values[3]]
        else:
            self.lastValue=values

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        del self.ADC

