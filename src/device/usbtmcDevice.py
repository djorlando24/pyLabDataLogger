"""
    USBTMC devices.
    
    Built on python-usbtmc, see:
    https://github.com/python-ivi/python-usbtmc
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 01/11/2018
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
import datetime, time, struct

try:
    import usbtmc
except ImportError:
    print "Please install usbtmc"
    raise

########################################################################################################################
class usbtmcDevice(device):
    """
        USBTMC device support.
    """

    def __init__(self,params={},quiet=False):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        # Check device is present on the bus.
        if 'bcdDevice' in self.params.keys():
            usbCoreDev = usb.core.find(idVendor=self.params['vid'],idProduct=self.params['pid'],\
                             bcdDevice=self.params['bcdDevice'])
        else:
            usbCoreDev = usb.core.find(idVendor=self.params['vid'],idProduct=self.params['pid'])
        
        if usbCoreDev is None:
            raise IOError("USB Device %s not found" % self.params['name'])

        # Parse driver parameters
        self.driver = self.params['driver'].lower().split('/')[0]
        self.bus = usbCoreDev.bus
        self.adds = usbCoreDev.address
        self.name = self.params['name']
        
        else: self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
        
        # Open channel to device
        self.instr =  usbtmc.Instrument(self.params['vid'],idProduct=self.params['pid'])
        self.driverConnected = True
        
        # Try and get ID of device as a check for successful connection
        try:
            self.params['IDN'] = self.instr.ask("*IDN?")
            print "\tdetected %s" % self.params['IDN']
            self.instr.ask("SYST:BEEP") # beep the interface
        except:
            self.params['IDN']='?'
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        if self.instr: del self.instr
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        subdriver = self.params['driver'].split('/')[1:]
        try:
            assert(self.deviceClass)
            if self.deviceClass is None: raise IOError
            
            # Apply subdriver-specific variable writes
            if subdriver=='?':
                #...
                pass
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])

        except IOError as e:
            print "\t%s communication error" % self.name
            print "\t",e
        except ValueError:
            print "%s - Invalid setting requested" % self.name
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

    # For oscilloscopes, sweep the channels for a certain parameter stored under
    # SCPI command :CHAN<n.:CMD
    def scope_channel_params(self,cmd):
        return np.array([self.instr.ask(":CHAN%1i:%s?" % (n,cmd)) for n in range(self.params['n_channels'])])

    # Configure device based on what sub-driver is being used.
    # This is done when self.query(reset=True) is called, as at
    # this point we might need to poll the device to check a setting.
    def configure_device(self):
        if self.subdriver=='33220a':
            
            # Check the mode
            self.params['mode'] = self.instr.ask('FUNC?')
        
            self.name = "Agilent 33220A function generator - %s" % self.params['IDN']
            self.config['channel_names']=['frequency','amplitude','phase','offset','duty cycle']
            self.params['raw_units']=['Hz','V','deg','V','']
            self.config['eng_units']=['Hz','V','deg','V','']
            self.config['scale']=[1.,1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.,0.]
            self.params['n_channels']=len(self.config['channel_names'])
            self.tmcQuery=['FREQ?','VOLT?','DEV?','VOLT:OFFS?','FUNC:%s:DCYC?' % self.params['mode']]
        
            # Now try to set the units more specifically
            self.params['raw_units'][1] = self.instr.ask("VOLT:UNIT?")
            self.config['eng_units'][1] = self.params['raw_units'][1]
            self.params['raw_units'][2] = self.instr.ask("UNIT:ANGL?")
            self.config['eng_units'][2] = self.params['raw_units'][2]
            
            # Get some other parameters that won't change often.
            self.params['Trigger source'] = self.instr.ask("TRIG:SOUR?")
            
        elif self.subdriver=='rigol-ds':
        
            # First let's put the device in SINGLE SHOT mode
            self.instr.write(":SING")
            # Now tell the scope to write waveforms in a known format
            self.instr.write(":WAV:MODE RAW") # return what's in memory
            self.instr.write(":WAV:FORM BYTE") # one byte per 8bit sample
            # self.instr.ask(":RUN")
        
            self.name = "Rigol DS Oscilloscope - %s" % self.params['IDN']
            self.config['channel_names']=['Ch1','Ch2','Ch3','Ch4']
            self.params['raw_units']=['V','V','V','V']
            self.config['eng_units']=['V','V','V','V']
            self.config['scale']=[1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.]
            self.params['n_channels']=len(self.config['channel_names'])
            self.tmcQuery=[':WAV:SOUR 1,:WAV:DATA?',':WAV:SOUR 1,:WAV:DATA?',':WAV:SOUR 1,:WAV:DATA?',':WAV:SOUR 1,:WAV:DATA?']
        
            # Get some parameters that don't change often
            self.params['Samples_per_sec'] = self.instr.ask(":ACQ:SRAT?")
            self.params['Seconds_per_div'] = self.instr.ask(":TIM:SCAL?")
            self.params['Bandwidth Limit'] = self.scope_channel_params("BWL")
            self.params['Coupling'] = self.scope_channel_params("COUP")
            self.params['Voltage Scale'] = self.scope_channel_params("SCAL")
            self.params['Active channels'] = self.scope_channel_params("DISP")
            self.params['Inverted'] = self.scope_channel_params("INV")
            self.params['Vertical Offset'] = self.scope_channel_params("OFFS")
            self.params['Vertical Range'] = self.scope_channel_params("RANG")
        
            # Get some waveform parameters
            for n in range(self.params['n_channels']):
                self.instr.write(":WAV:SOUR %1i" % n)
                time.sleep(0.01)
                self.params['Ch%i Waveform Parameters' % n] = self.instr.ask(":WAV:PRE?").split(',')
                time.sleep(0.01)
        
        
        else:
            raise KeyError("I don't know what to do with a device driver %s" % self.params['driver'])
        return

    # Convert incoming data stream to numpy array
    def convert_to_array(self,data):
        if self.subdriver=='33220a':
            return np.array(data)
        elif self.subdriver=='rigol-ds':
            return np.array( struct.unpack(data,'<b'), dtype=np.uint8 )
        else: raise KeyError("I don't know what to do with a device driver %s" % self.params['driver'])
        return None
        

    # Read latest values
    def get_values(self):
        try:
            rawData=[]
            for n in range(len(self.tcmQuery)): # loop channels
                # Commands to setup acquisiton are delimited by commas.
                if not ',' in self.tcmQuery[n]: q = self.tcmQuery[n] # no setup ocmmands
                else:
                    qs = self.tcmQuery[n].split(',') # split commands up
                    for q in qs[:-1]:
                        self.instr.write(q) # send setup commands with 10ms delay
                        time.sleep(0.01)
                    q = qs[-1]
                rawData.append(self.instr.ask(q)) # request data
            self.lastValue = self.convert_to_array(rawData)

        except IOError as e:
            print "\t%s communication error" % self.name
            print "\t",e

        return [np.nan]*self.params['n_channels']

    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.instr)
            if self.instr is None: raise IOError
        except:
            print "Connection to the device is not open."

        # If first time or reset, get configuration (ie units)
        if not 'raw_units' in self.params.keys() or reset:
            driver = self.params['driver'].split('/')[1:]
            self.subdriver = driver[0].lower()
            self.configure_device()

        # Read values        
        self.get_values()

        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


