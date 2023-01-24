#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    USBTMC devices.
    
    Built on python-usbtmc, see:
    https://github.com/python-ivi/python-usbtmc
    
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

from .device import device
from .device import pyLabDataLoggerIOError
import numpy as np
import datetime, time, struct, sys
from termcolor import cprint

try:
    import usbtmc
except ImportError:
    cprint( "Please install usbtmc", 'red', attrs=['bold'])
    raise
    
try:
    import usb.core
except ImportError:
    cprint( "Please install pyUSB", 'red', attrs=['bold'])
    raise

########################################################################################################################
class usbtmcDevice(device):
    """
        USBTMC device support.
        
        The usbtmc driver provides the following subdriver modules:
            'usbtmc/thorlabs-tsp01' : Thorlabs TSP01 temperature and humidity probe
            'usbtmc/thorlabs-pm'    : Thorlabs PM series power meters
            'usbtmc/33220a'         : Agilent 33220A function generator via USB
            'usbtmc/rigol-ds'       : Rigol DS series oscilloscopes. Not reliable, suggest using sigrok or pyvisa drivers instead.
            'usbtmc/dg1000z'        : Rigol DG1000Z programmable delay/function generator
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        
        self.driver = self.params['driver'].lower().split('/')[0]
        self.name = self.params['name']
        self.subdriver = self.params['driver'].split('/')[1].lower()
        
        if 'debugMode' in kwargs: self.debugMode = kwargs['debugMode']
        else: self.debugMode=False
        
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
            raise pyLabDataLoggerIOError("USB Device %s not found" % self.params['name'])
        else:
            self.bus = usbCoreDev.bus
            self.adds = usbCoreDev.address
            self.activate(quiet=quiet)
        
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
    
        # Open channel to device
        self.instr =  usbtmc.Instrument(self.params['vid'],self.params['pid'])
        self.instr.timeout = 2
        self.driverConnected = True
        
        # Reset device
        try:
            if self.subdriver=='thorlabs-tsp01':
                #self.write("*CLS\r") # clear status
                self.write("*RST\r") # reset
            else:
                self.instr.clear()
        except usbtmc.usbtmc.UsbtmcException as e:
            cprint( '\t%s' % e, 'red', attrs=['bold'])

        # Try and get ID of device as a check for successful connection
        try:
            self.params['IDN'] = self.ask("*IDN?")
            cprint( "\tdetected %s" % self.params['IDN'] ,'green')
            if self.subdriver=='33220a' or self.subdriver=='dg1000z': 
                self.write("SYST:BEEP") # beep the interface
        except KeyboardInterrupt: raise
        except:
            self.params['IDN']='?'
            if not quiet: cprint( '[no response]\n', 'yellow', attrs=['bold'])
                    
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        if self.instr:
            self.instr.close()
            del self.instr
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        try:
            assert(self.deviceClass)
            if self.deviceClass is None: raise pyLabDataLoggerIOError("Could not access device.")
            
            # Apply subdriver-specific variable writes
            if self.subdriver=='33220a':
                # Currently this is a read-only device. In future we could set the delay time etc. from here.
                pass
            if self.subdriver=='rigol-ds':
                # Currently this is a read-only device. In future we could set the sample rates etc.
                pass
            if self.subdriver=='thorlabs-tsp01':
                # Read only device
                pass
            if self.subdriver=='dg1000z':
                # Currently this is a read-only device. In future we could set the delay time etc. from here.
                pass

            else:
                raise KeyError("I don't know what to do with a device driver %s" % self.params['driver'])
    
        except ValueError:
            cprint( "%s - Invalid setting requested" % self.name, 'red', attrs=['bold'])
        
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
        else: cprint( "Error resetting %s: device is not detected" % self.name , 'red', attrs=['bold'])

    # Ask a command and get a response. Print debugging info if required
    def ask(self,cmd):
        if cmd=='' or cmd is None: return None
        if self.debugMode: 
            sys.stdout.write('\t%s\t' % cmd)
            sys.stdout.flush()
        assert(self.instr)
        response=""
        time.sleep(0.001)
        response = self.instr.ask(cmd+'\r\n') #.strip()
        if self.debugMode:
            sys.stdout.write('%s\n' % response)
            sys.stdout.flush()
        return response
        
    # Write a command with no response. Print debugging info if required
    def write(self,cmd):
        if self.debugMode: 
            sys.stdout.write('\t%s ' % cmd)
            sys.stdout.flush()
        assert(self.instr)
        self.instr.write(cmd)
        if self.debugMode:
            sys.stdout.write('.\n')
            sys.stdout.flush()
        return
        

    # For oscilloscopes, sweep the channels for a certain parameter stored under
    # SCPI command :CHAN<n.:CMD
    def scope_channel_params(self,cmd):
        return np.array([self.ask(":CHAN%1i:%s?" % (n,cmd)) for n in range(1,self.params['n_channels']+1)])

    # Configure device based on what sub-driver is being used.
    # This is done when self.query(reset=True) is called, as at
    # this point we might need to poll the device to check a setting.
    def configure_device(self):
        if self.subdriver=='33220a':
            
            # Check the mode
            self.params['mode'] = self.ask('FUNC?')
            
            self.name = "Agilent 33220A function generator - %s" % self.params['IDN']
            self.config['channel_names']=['frequency','amplitude','offset','duty cycle','pulse width']
            self.params['raw_units']=['Hz','V','V','','s']
            self.config['eng_units']=['Hz','V','V','','s']
            self.config['scale']=[1.,1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.,0.]
            self.params['n_channels']=len(self.config['channel_names'])
            if 'PULS' in self.params['mode']:
                self.tmcQuery=['FREQ?','VOLT?','VOLT:OFFS?','FUNC:PULS:DCYC?', 'FUNC:PULS:WIDT?']
            elif 'SQU' in self.params['mode']:
                self.tmcQuery=['FREQ?','VOLT?','VOLT:OFFS?','FUNC:SQU:DCYC?', None]
            else:
                self.tmcQuery=['FREQ?','VOLT?','VOLT:OFFS?',None, None]
                
            # Now try to set the units more specifically
            self.params['raw_units'][1] = self.ask("VOLT:UNIT?")
            self.config['eng_units'][1] = self.params['raw_units'][1]
            #self.params['raw_units'][4] = self.ask("UNIT:ANGL?")
            #self.config['eng_units'][4] = self.params['raw_units'][4]
            
            # Get some other parameters that won't change often.
            self.params['Trigger source'] = self.ask("TRIG:SOUR?")
            
        elif self.subdriver=='rigol-ds':
        
            # First let's put the device in SINGLE SHOT mode
            #self.write(":SING")
            # Now tell the scope to write waveforms in a known format
            self.write(":WAV:MODE RAW") # return what's in memory
            self.write(":WAV:FORM BYTE") # one byte per 8bit sample
            #self.ask(":RUN")
        
            self.name = "Rigol DS Oscilloscope - %s" % self.params['IDN']
            self.config['channel_names']=['Ch1','Ch2','Ch3','Ch4']
            self.params['raw_units']=['V','V','V','V']
            self.config['eng_units']=['V','V','V','V']
            self.config['scale']=[1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.]
            self.params['n_channels']=len(self.config['channel_names'])
            self.tmcQuery=[':WAV:SOUR 1,:WAV:DATA?',':WAV:SOUR 2,:WAV:DATA?',':WAV:SOUR 3,:WAV:DATA?',':WAV:SOUR 4,:WAV:DATA?']
        
            # Get some parameters that don't change often
            self.params['Samples_per_sec'] = self.ask(":ACQ:SRAT?")
            self.params['Seconds_per_div'] = self.ask(":TIM:SCAL?")
            self.params['Bandwidth Limit'] = self.scope_channel_params("BWL")
            self.params['Coupling'] = self.scope_channel_params("COUP")
            self.params['Voltage Scale'] = self.scope_channel_params("SCAL")
            self.params['Active channels'] = self.scope_channel_params("DISP")
            self.params['Inverted'] = self.scope_channel_params("INV")
            self.params['Vertical Offset'] = self.scope_channel_params("OFFS")
            self.params['Vertical Range'] = self.scope_channel_params("RANG")
        
            # Get some waveform parameters
            for n in range(self.params['n_channels']):
                self.write(":WAV:SOUR %1i" % n)
                time.sleep(0.01)
                self.params['Ch%i Waveform Parameters' % n] = self.ask(":WAV:PRE?").split(',')
                time.sleep(0.01)
        
        elif self.subdriver=='thorlabs-tsp01':        
            self.name = "Thorlabs TSP01 Thermometer/Barometer - %s" % self.params['IDN']
            self.config['channel_names']=['T1','T2','T_internal','Humidity']
            self.params['raw_units']=['degC','degC','degC','%']
            self.config['eng_units']=['degC','degC','degC','%']
            self.config['scale']=[1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.]
            self.params['n_channels']=len(self.config['channel_names'])            
            self.tmcQuery=['SENS3:TEMP:DATA?','SENS4:TEMP:DATA?','SENS1:TEMP:DATA?','SENS2:HUM:DATA?']

        elif self.subdriver=='thorlabs-pm':        
            self.name = "Thorlabs pm Power Meter - %s" % self.params['IDN']
            self.config['channel_names']=['Current','Power']
            self.params['n_channels']=len(self.config['channel_names'])
            self.params['raw_units']=['A','W']
            self.config['eng_units']=['uA','mW']
            self.config['scale']=[1e6,1e3]
            self.config['offset']=[0.]*self.params['n_channels']

            self.tmcQuery=['CONF:CURR,Read?','CONF:POW,Read?']
            
            # Set auto ranging by default
            self.write("SENS:POW:RANG:AUTO ON")
            #self.config['auto ranging'] = self.ask('SENS:CURR:RANGE:AUTO?')

            # Get system parameters
            #self.params['frequency'] = self.ask("MEAS:FREQ?") # PM16 does not support
            #self.params['attenuation'] = 'SENS:CORR:LOSS:INP:MAGN?' # PM16 does not support
            self.params['wavelength'] = self.ask("SENS:CORR:WAV?")+' nm'
            self.params['zero magnitude'] = self.ask("SENS:CORR:COLL:ZERO:MAGN?")
            self.params['zero state'] = self.ask("SENS:CORR:COLL:ZERO:STAT?")            
            self.params['photodiode response'] =self.ask("SENS:CORR:POW:PDIOde:RESP?")+' A/W'
            #self.params['averaging'] = self.ask("SENS:AVER:COUNt?") # PM16 does not support
            
        elif self.subdriver=='dg1000z':
            self.config['channel_names']=[]
            for n in range(1,3): self.config['channel_names'].extend(['CH%i_type' % n,\
                                                                    'CH%i_frequency' % n,\
                                                                    'CH%i_amplitude' % n,\
                                                                    'CH%i_offset' % n,\
                                                                    'CH%i_phase' % n,\
                                                                    'CH%i_pulse_width' % n,\
                                                                    'CH%i_burst' % n,\
                                                                    'CH%i_burst_delay' % n])
            self.params['n_channels']=len(self.config['channel_names'])
            self.params['raw_units']=['']*self.params['n_channels']
            self.config['eng_units']=['']*self.params['n_channels']
            self.config['scale']=[1.]*self.params['n_channels']
            self.config['offset']=[0.]*self.params['n_channels']
            # :SOURx:APPL? will return type, frequency, amplitude, offset and phase in one string.
            self.tmcQuery = [':SOUR1:APPL?',':SOUR1FUNC:PULS:WIDT?',':SOUR1:BURS:STAT?',':SOUR1:BURS:TDEL?',\
                             ':SOUR2:APPL?',':SOUR2FUNC:PULS:WIDT?',':SOUR2:BURS:STAT?',':SOUR2:BURS:TDEL?']
            
        else:
            print(self.__doc__)
            raise KeyError("I don't know what to do with a device driver %s" % self.params['driver'])
        return

    # Convert incoming data stream to numpy array
    def convert_to_array(self,data):
        if self.subdriver=='33220a':
            return np.array(data,dtype=np.float32)
        elif self.subdriver=='rigol-ds':
            return np.array( struct.unpack(data,'<b'), dtype=np.uint8 )
        elif self.subdriver=='thorlabs-tsp01':
            return np.array([float(v) for v in data])
        elif self.subdriver=='thorlabs-pm':
            return np.array([float(v) for v in data])
        elif self.subdriver=='dg1000z':
            print(data)
            raise RuntimeError
        else: raise KeyError("I don't know what to do with a device driver %s" % self.params['driver'])
        return None
        

    # Read latest values
    def get_values(self):
        rawData=[]
        for n in range(len(self.tmcQuery)): # loop channels
            # Commands to setup acquisiton are delimited by commas.
            if not ',' in self.tmcQuery[n]: q = self.tmcQuery[n] # no setup commands
            else:
                qs = self.tmcQuery[n].split(',') # split commands up
                for q in qs[:-1]:
                    self.write(q) # send setup commands with 10ms delay
                    time.sleep(0.01)
                q = qs[-1]
            try:
                if q != '':
                    rawData.append(self.ask(q)) # request data
                else:
                    rawData.append(self.instr.read()) # expect data
            except KeyboardInterrupt: raise
            except:
                rawData.append(np.nan) # failed to get data
                if self.debugMode: cprint( "[no response]\n", 'red', attrs=['bold'])

        
        self.lastValue = self.convert_to_array(rawData)

        return [np.nan]*self.params['n_channels']

    
    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.instr)
            if self.instr is None: raise pyLabDataLoggerIOError("Could not access device.")
        except:
            cprint( "Connection to the device is not open.", 'red', attrs=['bold'])

        # For 33220a, if the mode has changed we will need to reset the configuration.
        if self.subdriver=='33220a' and 'mode' in self.params:
            if self.ask('FUNC?') != self.params['mode']:
                reset=True
                if self.debugMode: cprint( "\tFunction mode switch detected", 'yellow' )
            

        # If first time or reset, get configuration (ie units)
        if not 'raw_units' in self.params.keys() or reset:
            self.configure_device()

        # Read values        
        self.get_values()
        
        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * np.array(self.config['scale']) + np.array(self.config['offset'])
        self.updateTimestamp()
        return self.lastValue


