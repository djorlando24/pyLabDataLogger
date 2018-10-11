"""
    Serial device class - general serial port support and arduino-like device support
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 1.0.0
    @date 06/06/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from device import device
import numpy as np
import datetime, time

try:
    import serial
except ImportError:
    print "Please install pySerial"
    raise

########################################################################################################################
class serialDevice(device):
    """ Class providing support for any tty type serial device. """

    def __init__(self,params={}):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "untitled Serial device"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.Serial = None
        if params is not {}: self.scan()
        
        return

    # Detect if device is present
    def scan(self,override_params=None):
        self.port = None
        if override_params is not None: self.params = override_params
        
        # Find the tty associated with the serial port
        if 'tty' in self.params.keys():
            self.port = self.params['tty']
        elif 'port' in self.params.keys():
            self.port = self.params['port']
        elif 'pid' in self.params.keys() and 'vid' in self.params.keys(): # USB serial
            
            from serial.tools import list_ports
            for serialport in list_ports.comports():
                if serialport.vid==self.params['vid'] and serialport.pid==self.params['pid']:
                    print '\t',serialport.hwid, serialport.name
                    self.port = serialport.name
                    self.params['tty']=serialport.name
                    
        if self.port is None: print "Unable to connect to serial port - port unknown."
        else: self.activate()
        return

    # Establish connection to device (ie open serial port)
    def activate(self):
        if not 'baudrate' in self.params.keys(): self.params['baudrate']=9600
        if not 'bytesize' in self.params.keys(): self.params['bytesize']=serial.EIGHTBITS
        if not 'parity' in self.params.keys(): self.params['parity']=serial.PARITY_NONE
        if not 'stopbits' in self.params.keys(): self.params['stopbits']=serial.STOPBITS_ONE
        if not 'xonxoff' in  self.params.keys(): self.params['xonxoff']=False
        if not 'rtscts' in  self.params.keys(): self.params['rtscts']=False
        self.Serial = serial.Serial(port=self.port, baudrate=self.params['baudrate'],\
                                    bytesize=self.params['bytesize'], parity=self.params['parity'],\
                                    stopbits=self.params['stopbits'], xonxoff=self.params['xonxoff'],\
                                    rtscts=self.params['rtscts'])
                                    
        # Make first query to get units, description, etc.
        print self.query(reset=True), self.config['eng_units'], self.params['channel_names']
        
        import time
        for n in range(10):
            time.sleep(1)
            print self.query()
        
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        self.Serial.close()
        return

    # Apply configuration changes to the driver
    def apply_config(self):
        self.reset()

    # Update configuration (ie change sample rate or number of samples)
    def update_config(self,config_keys={}):
        for key in config_keys.keys():
            self.config[key]=self.config_keys[key]
        self.apply_config()
        return

    def updateTimestamp(self):
        self.lastValueTimestamp = datetime.datetime.now()

    # Re-establish connection to device.
    def reset(self):
        self.deactivate()
        self.scan()
        if self.driverConnected: self.activate()
        else: print "Error resetting %s: device is not detected" % self.name



########################################################################################################################
class arduinoSerialDevice(serialDevice):
    """ Class defining an Arduino type microcontroller that communicates over the serial
        port, typically via USB. """

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self, reset=False, buffer_limit=1024):
    
        # Check
        try:
            assert(self.Serial)
            if self.Serial is None: raise IOError
        except:
            print "Serial connection to Arduino device is not open."
        
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
        if not 'channel_names' in self.params.keys() or reset:
            reset=True
            self.params['channel_names']=[]
            self.params['raw_units']=[]
            self.config['eng_units']=[]
            self.params['n_channels']=0
            self.name = desc
            print '\t',self.name
    
            while self.config['eng_units'] == []:
                nbytes=0; s=''
                while nbytes<buffer_limit:
                    s+=self.Serial.read(1)
                    if s[-1] == '=':
                        self.params['channel_names'].append(s[:-2].strip())
                        self.params['n_channels']+=1
                        break
                    nbytes+=1
                
                nbytes=0; s=''
                while nbytes<buffer_limit:
                    s+=self.Serial.read(1)
                    if s[-1] == ' ' and len(s)>1:
                        values.append( float(s.strip()) )
                        break
                    nbytes+=1
                
                nbytes=0; s=''
                while nbytes<buffer_limit:
                    s+=self.Serial.read(1)
                    if s[-1] == ',' or s[-1] == '\n':
                        self.params['raw_units'].append( s[:-1].strip() )
                        break
                    nbytes+=1
                
                if s[-1] == '\n':
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
