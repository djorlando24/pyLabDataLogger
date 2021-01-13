"""
    Tenma serial communications devices
    
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
class tenmaPowerSupplySerialDevice(serialDevice):
    """ Class for TENMA 72-2710 power supply communicating via serial port.
        It has one output channel with two variables (V and I). 

        By default we assume that the ttys can be found in /dev (*nix OS)
        However this can be overridden by passing 'port' or 'tty' directly
        in the params dict."""

    def __init__(self,params={},tty_prefix='/dev/',quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        if '/' in self.params['driver']:
            self.driver = self.params['driver'].split('/')[1:]
            self.subdriver = self.driver[0].lower()
        else:
            self.driver = self.params['driver']
            self.subdriver = 'None'
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.Serial = None
        self.tty_prefix = tty_prefix
        self.name=params['name']
        self.params['baudrate']=115200
        self.config['channel_names']=['Voltage','Current']
        self.params['raw_units']=['V','A']
        self.config['eng_units']=['V','A']
        self.config['scale']=[1.,1.]
        self.config['offset']=[0.,0.]
        self.config['set_voltage']=None
        self.config['set_current']=None
        self.params['n_channels']=2
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet = quiet
        if params is not {}: self.scan()
        
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self, reset=False, timeout=10):
        
        # Check
        try:
            assert(self.Serial)
            if self.Serial is None: raise pyLabDataLoggerIOError("Could not open serial port to device")
        except:
            cprint( "Serial connection to TENMA device is not open.", 'red', attrs=['bold'])
    
        # First pass
        if not 'channel_names' in self.params.keys() or reset:
            reset=True
            
            self.Serial.write("*IDN?\n")
            time.sleep(0.01)
            s=''
            while len(self.name)<64:
                s += self.Serial.read(1)
                if s[-1] == '\n':
                    self.params['ID'] = s[:-1]
                    break
    
            # Get setpoints
            s=''
            self.Serial.write("VSET1?\n")
            time.sleep(0.01)
            while len(s)<1024:
                s+=self.Serial.read(1)
                if s[-1] == '\n':
                    self.params['set_voltage']=float(s.strip())
                    break
            
            s=''
            self.Serial.write("ISET1?\n")
            time.sleep(0.01)
            while len(s)<1024:
                s+=self.Serial.read(1)
                if s[-1] == '\n':
                    self.params['set_current']=float(s.strip())
                    break
            
            #On first pass or reset, show user the set points are recorded
            if not self.quiet:
                print( "\tVSET1 = %s" % self.params['set_voltage'] )
                print( "\tISET1 = %s" % self.params['set_current'] )
        
        # Get values
        self.lastValue=[]
        s=''
        self.Serial.write("VOUT1?\n")
        time.sleep(0.01)
        while len(s)<1024:
            s+=self.Serial.read(1)
            if s[-1] == '\n':
                self.lastValue.append(float(s.strip()))
                break
        s=''
        self.Serial.write("IOUT1?\n")
        time.sleep(0.01)
        while len(s)<1024:
            s+=self.Serial.read(1)
            if s[-1] == '\n':
                self.lastValue.append(float(s.strip()))
                break
    
    

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']

        return self.lastValue

    # Apply configuration changes to the driver (ie set point voltage and current)
    def apply_config(self):
        try:
            assert(self.Serial)
            if self.Serial is None: raise pyLabDataLoggerIOError("Could not open serial port to device")
            self.Serial.write("VSET1:%0f\n" % float(self.config['set_voltage']))
            self.Serial.write("ISET1:%0f\n" % float(self.config['set_current']))
            self.query(reset=True)
        except ValueError:
            cprint( "%s - Invalid set point requested" % self.name, 'red', attrs=['bold'])
            cprint( "\t(V=%s  I=%s)" % (self.config['set_voltage'],self.config['set_current']),'red')
        
        return

