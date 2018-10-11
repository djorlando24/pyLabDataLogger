"""
    Serial device class - general serial port support
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 11/10/2018
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
    """ Class providing support for any tty type serial device. 
        By default we assume that the ttys can be found in /dev (*nix OS)
        However this can be overridden by passing 'port' or 'tty' directly
        in the params dict.
    """

    def __init__(self,params={},tty_prefix='/dev/'):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "untitled Serial device"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.Serial = None
        self.tty_prefix = tty_prefix
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
                    self.port = self.tty_prefix + serialport.name
                    self.params['tty']=self.port
                    
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




