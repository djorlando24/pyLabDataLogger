"""
    Tenma serial communications devices
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 29/11/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from serialDevice import serialDevice
from device import pyLabDataLoggerIOError
import numpy as np
import datetime, time

try:
    import serial
except ImportError:
    print "Please install pySerial"
    raise

########################################################################################################################
class tenmaPowerSupplySerialDevice(serialDevice):
    """ Class for TENMA 72-2710 power supply communicating via serial port.
        It has one output channel with two variables (V and I). 

        By default we assume that the ttys can be found in /dev (*nix OS)
        However this can be overridden by passing 'port' or 'tty' directly
        in the params dict."""

    def __init__(self,params={},tty_prefix='/dev/',**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
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
        if params is not {}: self.scan()
        
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self, reset=False, timeout=10):
        
        # Check
        try:
            assert(self.Serial)
            if self.Serial is None: raise pyLabDataLoggerIOError("Could not open serial port to device")
        except:
            print "Serial connection to TENMA device is not open."
    
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
            print "\tVSET1=",self.params['set_voltage'],"\tISET1=",self.params['set_current']
        
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
            print "%s - Invalid set point requested" % self.name
            print "\t(V=",self.config['set_voltage'],"I=", self.config['set_current'],")"
        
        return

