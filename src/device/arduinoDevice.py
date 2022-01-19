"""
    Serial device class - arduino like devices that talk over a USB to serial TTY
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2
    @date 19/01/2022
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

from .serialDevice import serialDevice
from .device import pyLabDataLoggerIOError
import numpy as np
import datetime, time
from termcolor import cprint

try:
    import serial
except ImportError:
    cprint( "Please install pySerial", 'red', attrs=['bold'])
    raise

########################################################################################################################
class arduinoSerialDevice(serialDevice):
    """ Class defining an Arduino type microcontroller that communicates over the serial
        port, typically via USB. """

    # Parse serial data
    def readArduinoString(self):
        try:
            s1 = self.Serial.readline()
            while (not b':' in s1) or (len(s1)<=3): s1 = self.Serial.readline()
            l = s1.decode('utf-8').split(':')
            desc=l[0]; varstr=l[1]
            if ',' in varstr: varlist=[s.strip() for s in varstr.split(',')]
            else: varlist=[varstr.strip()]
            
            #print(desc)
            varnames=[]
            values=[]
            varunits=[]
            
            for v in varlist:
                varname,valstr = v.split('=')
                value,units = valstr.strip().split(' ')
                value=float(value)
                #print('\t',[varname,value,units])
                varnames.append(varname)
                values.append(value)
                varunits.append(units)
            
        except UnicodeDecodeError:
            return None,None,None,None
        
        except:
            raise
            
        return desc,varnames,values,varunits

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self, reset=False, buffer_limit=1024):
    
        # Check
        try:
            assert(self.Serial)
            if self.Serial is None: raise pyLabDataLoggerIOError("Could not access serial port")
        except:
            cprint( "Serial connection to Arduino device is not open.", 'red', attrs=['bold'])
        
        # The serial arduino device should report repeated strings with the structure
        # DESCRIPTION: VARIABLE = VALUE UNITS, VARIABLE = VALUE UNITS\n
        
        # Increase the default timeout in case we have to wait a few seconds for the next full update.
        self.Serial.timeout=10

        # Check if we need to do setup
        first_loop = (not 'channel_names' in self.config.keys()) or reset
        if first_loop: 
            for n in range(2): 
                self.Serial.readline()
             
        # Attempt to get data
        desc=None
        while desc is None:
            desc,varnames,values,varunits = self.readArduinoString()

        # Do we update the device name?  (first time, or if string was broken during 1st reading)
        if first_loop or ((self.name in desc) and (len(desc)>len(self.name))):
            self.name=desc

        # update the channel names and units first time
        if first_loop:
            self.config['channel_names']=varnames
            self.params['n_channels']=len(varnames)
            self.params['raw_units']=varunits
            if not 'eng_units' in self.config.keys():
                self.config['eng_units']=varunits
            if not 'scale' in self.config.keys():
                self.config['scale'] = np.ones(self.params['n_channels'],)
            if not 'offset' in self.config.keys():
                self.config['offset'] = np.zeros(self.params['n_channels'],)
                
        # update channel names and units if there was a channel missing previous run due to a broken string
        if len(varnames)>len(self.config['channel_names']):
            self.config['channel_names']=varnames
            self.params['n_channels']=len(varnames)
            self.params['raw_units']=varunits
            for n in range(self.config['eng_units'], len(varnames)):
                self.config['eng_units'].append(varunits[n])
                self.config['scale'].append(1)
                self.config['offset'].append(0)
        
        # check size of arrays - pad with NaN if there was some IO error and data cut off.
        if len(values) != len(self.config['scale']):
            for n in range(len(values),len(self.config['scale'])):
                values.append(np.nan)
        
        self.lastValue = np.array(values)
        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        
        return self.lastValue
