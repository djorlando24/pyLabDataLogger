#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    MS5637 Piicodev pressure sensor
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 14/02/26

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



########################################################################################################################
class ms5637Device(i2cDevice):
    """ Class providing support for Piicodev MS5637 pressure sensor breakout boards.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        if not self.bridge: assert self.params['bus']
        else: assert self.params['tty']
        
        if not 'driver' in self.params.keys(): self.params['driver']='ms5637'
        if 'name' in self.params: self.name = self.params['name']+' %s' % (hex(self.params['address']))
        self.params['n_channels']=2
        if not 'channel_names' in self.config:
            self.config['channel_names']=['Temperature','Pressure']

        self.params['raw_units']=['hPa','degC']
        self.config['eng_units']=['kPa','degC']
        self.config['scale']=[0.1,1.0]
        self.config['offset']=[0.,0.]
        if 'gain' in self.params: self.config['gain']=self.params['gain']
        cprint( "Activating %s on i2c at %s with %i channels" % (self.params['driver'],hex(self.params['address']),self.params['n_channels']), 'green')

        # device specific configuration settings and variables
        self.config['resolution'] = 5
        self.eeprom_coeff = [0,0,0,0,0,0,0,0]
        self.coeff_valid = False
        
        if self.bridge:
            self.bridgeDev.start(self.params['address'],1)
            time.sleep(0.015)
            data=self.bridgeDev.write([0x1e]) # soft reset sensor. Resolution is set on query.
            self.bridgeDev.stop()
        else:
            raise RuntimeError("SMBUS implementation not done yet!")
        
        self.driverConnected=True
        
        return

    def setResolution(self,res) :
        """ Set resolution of the MS5637. 
            Valid options are 0--5, corresponding to 8--13 bit resolution respectively.
            Higher bits means longer adc conversion delay and slower read rate.
        """
        if res<0: res=abs(res)
        if res>5: res=5
        time = [1,2,3,5,9,17] # milliseconds for each setting
        cmd_temp = res *2;
        cmd_temp |= 0x50
        _time_temp = time[int((cmd_temp & 0x0f)/2)]
        cmd_pressure = res *2;
        cmd_pressure |= 0x40
        _time_pressure = time[int((cmd_pressure & 0x0f)/2)]
        return cmd_temp,cmd_pressure, _time_temp, _time_pressure
    
    def conversionRead(self,cmd,_time) :
        """ Send a command and read back data stored in ADC conversion memory """
        if self.bridge:
            self.bridgeDev.start(self.params['address'],0)
            self.bridgeDev.write(bytes([cmd]))
            self.bridgeDev.stop()
            time.sleep(_time/1000.)
            data = self.bridgeDev.regrd(self.params['address'], 0, 3)
            
        else:
            raise RuntimeError("SMBUS implementation not done yet!")
            
        return int.from_bytes(data, 'big')
    
    def readEEPromCoeff (self, cmd) :
        """ Read one EEPRom register from MS5637 """
        if self.bridge:
            data = self.bridgeDev.regrd(self.params['address'], cmd, 2)
        else:
            raise RuntimeError("SMBUS implementation not done yet!")
        return int.from_bytes(data, 'big')
    
    def readEEProm(self):
        """ Read EEPRom settings of MS5637 """
        a = 0
        coeffs = [0,0,0,0,0,0,0,0]
        registerList = [0xa0, 0xa2, 0xa4, 0xa6, 0xa8, 0xaa, 0xac]
        for i in registerList :
            coeffs[a] = self.readEEPromCoeff(i)
            a = a+1
        self.coeff_valid = True
        return coeffs
    
    def getTempAndPress(self,res=5):
        """ Read temperature and pressure and convert to human readable units. 
        Default to highest resolution, lowest speed option. """
        if self.coeff_valid == False :
            self.eeprom_coeff = self.readEEProm()
        (cmd_temp, cmd_pressure,_time_temp,_time_pressure) = self.setResolution(res)
        try:
            adcTemp = self.conversionRead(cmd_temp,_time_temp)
            adcPress = self.conversionRead(cmd_pressure,_time_pressure)
        except:
            # print error message?
            raise
            return None, None
        if ((type(adcTemp) is not int) or (type(adcPress) is not int)):
            return None, None
        # Difference between actual and reference temperature = D2 - Tref
        dT = (adcTemp) - (self.eeprom_coeff[5] * 0x100)
        # Actual temperature = 2000 + dT * TEMPSENS
        TEMP = 2000 + (dT * self.eeprom_coeff[6] >> 23);
        # Second order temperature compensation
        if TEMP < 2000 : 
            T2 = ( 3 * ( dT  * dT  ) ) >> 33
            OFF2 = 61 * (TEMP - 2000) * (TEMP - 2000) / 16 
            SENS2 = 29 * (TEMP - 2000) * (TEMP - 2000) / 16 
            if TEMP < -1500 :
                OFF2 += 17 * (TEMP + 1500) * (TEMP + 1500) 
                SENS2 += 9 * ((TEMP + 1500) * (TEMP + 1500))
        else :
            T2 = ( 5 * ( dT  * dT  ) ) >> 38
            OFF2 = 0 
            SENS2 = 0

        #  OFF = OFF_T1 + TCO * dT
        OFF = ( (self.eeprom_coeff[2]) << 17 ) + ( ( (self.eeprom_coeff[4]) * dT ) >> 6 ) 
        OFF -= OFF2 ;

        # Sensitivity at actual temperature = SENS_T1 + TCS * dT
        SENS = ( self.eeprom_coeff[1] * 0x10000 ) + ( (self.eeprom_coeff[3] * dT) >> 7 ) 
        SENS -= SENS2
        #  Temperature compensated pressure = D1 * SENS - OFF
        P = ( ( (int(adcPress * SENS)) >> 21 ) - int(OFF) ) >> 15 

        temperature = ( TEMP - T2 ) / 100.0 # degC
        pressure = P / 100.0 # hPa

        return pressure, temperature # in order that matches channel_names
    
    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        

        self.lastValue = self.getTempAndPress(res=self.config['resolution'])
        
        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        if self.bridge:
            self.bridgeDev.stop()
            del self.bridgeDev

