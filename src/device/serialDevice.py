"""
    Serial device class - general serial port support
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 12/10/2018
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

    def __init__(self,params={},tty_prefix='/dev/',quiet=False):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "untitled Serial device"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.Serial = None
        self.tty_prefix = tty_prefix
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
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
                    if not quiet: print '\t',serialport.hwid, serialport.name
                    self.port = self.tty_prefix + serialport.name
                    self.params['tty']=self.port
                    
        if self.port is None: print "Unable to connect to serial port - port unknown."
        else: self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
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
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        self.Serial.close()
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        subdriver = self.params['driver'].split('/')[1:]
        try:
            assert(self.Serial)
            if self.Serial is None: raise IOError

            # Apply subdriver-specific variable writes
            if subdriver=='omega-ir-usb':
                e=self.config['set_emissivity']
                if (e is not None) and (e>0) and (e<=1.): self.Serial.write("E%0.2f\n" % float(e))
                else: raise ValueError
            elif subdriver=='ohaus7k':
                # No settings can be modified at present. In future we could allow tare/zero or
                # a change of units.
                pass
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])

        except IOError:
            print "%s communication error" % self.name
        except ValueError:
            print "%s - Invalid set point requested" % self.name
            print "\t(V=",self.params['set_voltage'],"I=", self.params['set_current'],")"
        
        return

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

    # Configure device based on what sub-driver is being used.
    # This is done when self.query(reset=True) is called, as at
    # this point we might need to poll the device to check a setting.
    def configure_device(self):
        subdriver = self.subdriver
        if subdriver=='omega-ir-usb':
            self.config['channel_names']=['tempC','tempF','ambientC','ambientF','emissivity']
            self.params['raw_units']=['C','F','C','F','']
            self.config['eng_units']=['C','F','C','F','']
            self.config['scale']=[1.,1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.,0.]
            self.params['n_channels']=5
            self.serialQuery=['C','F','A','E']
            self.queryTerminator='\r\n'
            self.responseTerminator='\r'
            self.config['set_emissivity']=None
        elif subdriver=='ohaus7k':
            #Get the units currently set on the display
            s=''
            unit='?'
            self.Serial.write('PU\r\n')
            time.sleep(0.01)
            while len(s)<1024:
                s+=self.Serial.read(1)
                if s[-1] == '\r':
                    unit=s.strip()
                    break
            # Fixed settings.
            self.config['channel_names']=['weight']
            self.params['raw_units']=[unit]
            self.config['eng_units']=[unit]
            self.config['scale']=[1.]
            self.config['offset']=[0.]
            self.params['n_channels']=1
            self.serialQuery=['IP']
            self.queryTerminator='\r\n'
            self.responseTerminator='\r'
        else:
            raise KeyError("I don't know what to do with a device driver %s" % self.params['driver'])
        return

    # Convert string responses from serial port into usable numbers/values
    def convert_raw_string_to_values(self, rawData):
        subdriver = self.subdriver
        try:
            if subdriver=='omega-ir-usb':
                if len(rawData)<2: return [None]*self.params['n_channels']
                vals= [float(rawData[0].strip('>')), float(rawData[1].strip('>'))]
                if len(rawData)<3: vals.extend([np.nan, np.nan])
                else: vals.extend([float(v) for v in rawData[2].split('=')[1].split(',')])
                if len(rawData)<4: vals.append(np.nan)
                else: vals.append(float(rawData[3].split('=')[1]))
                return vals
            elif subdriver=='ohaus7k':
                vals=rawData[0].split(' ')
                self.params['raw_units']=[vals[-1].strip()]
                return [float(vals[0])]
            else:
                raise KeyError("I don't know what to do with a device driver %s" % self.params['driver'])
        except ValueError:
            print "Failure to unpack raw string from device:", rawData
        return [None]*self.params['n_channels']
    
    # Read latest values
    def get_values(self):
        try:
            rawData=[]
            for n in range(len(self.serialQuery)):

                # This method block is for devices that use a standard 
                # method; call<CR/LF> -short delay- response<CR/LF>.
                s=''
                self.Serial.write(self.serialQuery[n]+self.queryTerminator)
                time.sleep(0.01)
                while len(s)<1024:
                    s+=self.Serial.read(1)
                    if s[-1] == self.responseTerminator:
                        rawData.append(s.strip())
                        break
    
            self.lastValue = self.convert_raw_string_to_values(rawData)

        except IOError:
            print "%s communication error" % self.name
            return None

        return


    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.Serial)
            if self.Serial is None: raise IOError
        except:
            print "Serial connection to the device is not open."

        # If first time or reset, get configuration
        if not 'raw_units' in self.params.keys() or reset:
            driver = self.params['driver'].split('/')[1:]
            self.subdriver = driver[0].lower()
            self.configure_device()
        
        self.get_values()
        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


