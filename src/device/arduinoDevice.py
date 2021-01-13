"""
    Serial device class - arduino like devices that talk over a USB to serial TTY
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.1
    @date 13/01/2021
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

from serialDevice import serialDevice
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
        
        nbytes=0
        desc=''
        while nbytes<buffer_limit:
            desc += self.Serial.read(1)
            if desc[-1] == ':':
                desc=desc[:-1]
                break
            nbytes+=1

        # First pass?
        values=[]
        if not 'channel_names' in self.config.keys() or reset:
            reset=True
            self.config['channel_names']=[]
            self.params['raw_units']=[]
            self.config['eng_units']=[]
            self.params['n_channels']=0
            self.name = desc
            cprint( '\t'+self.name, 'green')
    
            while self.config['eng_units'] == []:
                nbytes=0; s=''
                while nbytes<buffer_limit:
                    s+=self.Serial.read(1)
                    if s[-1] == '=':
                        self.config['channel_names'].append(s[:-2].strip())
                        self.params['n_channels']+=1
                        break
                    nbytes+=1
                
                nbytes=0; s=''
                while nbytes<buffer_limit:
                    s+=self.Serial.read(1)
                    if ((s[-1] == ' ') or (s[-1] == '\r') or (s[-1] == '\n')) and len(s)>1:
                        values.append( float(s.strip()) )
                        break
                    nbytes+=1
                
                nbytes=0; s=''
                while nbytes<buffer_limit:
                    s+=self.Serial.read(1)
                    if s[-1] == ',' or s[-1] == '\r' or s[-1] == '\n':
                        self.params['raw_units'].append( s[:-1].strip() )
                        break
                    nbytes+=1
                
                if s[-1] == '\n' or s[-1] == '\r':
                    self.config['eng_units']=self.params['raw_units']
                    break
                elif s[-1] != ',':
                    while self.Serial.read(1) != ',': pass

            if not 'scale' in self.config.keys():
                self.config['scale'] = np.ones(self.params['n_channels'],)
            if not 'offset' in self.config.keys():
                self.config['offset'] = np.zeros(self.params['n_channels'],)


        else:
            # Repeat query, no need to worry about the description and variable names
            nbytes=0; s=''; invar=False
            while nbytes<buffer_limit:
                s+=self.Serial.read(1)
                if s[-1] == '=':
                    s=''; nbytes=0
                    invar=True
                    s+=self.Serial.read(1)
                if s[-1] == ' ' and invar and len(s) > 1:
                    values.append( float(s.strip()) )
                    s=''; nbytes=0
                    invar=False
                    s+=self.Serial.read(1)
                if s[-1] == '\n': break
                nbytes+=1
    
        self.lastValue = np.array(values)
        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        
        return self.lastValue
