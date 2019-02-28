#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pyVISA-py device class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 28/02/2019
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from device import device, pyLabDataLoggerIOError
import numpy as np
import datetime, time, sys, struct

try:
    import visa
except ImportError:
    print "Please install pyvisa-py"
    raise

########################################################################################################################
class pyvisaDevice(device):
    """ Class providing support for pyVISA-py devices.
    
        This class was written primarily for driverless VISA device access over TCP/IP, but can also theoretically be used
        for USB VISA devices. However, pyLabDataLogger supports a range of USB devices by other means such as usbtmc and you
        should check those first.
    
        This class supports two main drivers, 'pyvisa' and 'nivisa' depending on which backed you want to use. 'pyvisa' should
        be the default, as it uses a pure python open source implementation. 'nivisa' requires a seperate install of the
        NI-VISA dynamic libraries, which pyLabDataLogger does not provide.
        
        The following subdriver modules are supported through either 'pyvisa' or 'nivisa':
            'pyvisa/dg1000z' : Rigol DG1000Z programmable delay/function generator
            'pyvisa/ds1000z' : Rigol DS1000Z oscilloscope
            'pyvisa/33220a'  : Agilent 33220A programmable delay/function generator
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.driver = self.params['driver']
        self.name = "pyVISA-py device %s" % self.driver
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet
        
        self.subdriver = ''.join(self.params['driver'].split('/')[1:])
        
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        if 'pyvisa' in self.driver:
            self.rm = visa.ResourceManager('@py') # Open source pure-python pyVISA backend
        elif 'nivisa' in self.driver:
            self.rm = visa.ResourceManager('@ni') # National instruments closed source backend, if required!
        else:
            raise ValueError("Unknown backend driver. Choices are pyvisa or nivisa.")

        assert(self.rm)
        
        if not 'resource' in self.params:
            print "pyVISA-py: Please specify a resource. Possible resources include but not limited to:"
            print self.rm.list_resources()
            print "Network device resources can usually be determined by browsing to the device's IP address or checking the Network Settings control panel on the device."
            return
        
        self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
    
        self.inst = self.rm.open_resource(self.params['resource'],timeout=30000)
        self.driverConnected=True
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        
        del self.inst
        self.driverConnected=False
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        try:
            assert(self.deviceClass)
            if self.deviceClass is None: raise pyLabDataLoggerIOError("Could not access device.")
            
            # Apply subdriver-specific variable writes
            if self.subdriver=='dg1000z':
                # currently no writeable options supported.
                # in future could alter the DG settings from here.
                pass
            elif self.subdriver=='ds1000z':
                # in future could alter the time/voltage range/acq settings from here.
                
                # Check to see if any new channels were activated/deactivated!
                # Find out which channels are turned on, just acquire those.
                self.serialQuery=[]
                self.params['Active channels']=[]
                for nch in range(1,self.params['n_channels']+1):
                    channel_active = int(self.instrumentQuery(":CHAN%1i:DISP?" % nch).strip())
                    self.params['Active channels'].append(channel_active)
                    if channel_active == 1:
                        self.serialQuery.append(":WAV:SOUR %i,:WAV:DATA?" % nch)
                    else:
                        self.serialQuery.append(None)
                
            elif self.subdriver=='33220a':
                # currently no writeable options supported.
                # in future could alter the DG settings from here.
                pass
            else:
                print self.__doc__
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        
        except ValueError:
            print "%s - Invalid setting requested" % self.name
        
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
        assert(self.inst)
        l=[]
        for n in range(1,self.params['n_channels']+1):
            v=self.instrumentQuery(":CHAN%1i:%s?" % (n,cmd)).strip()
            try: v=float(v)
            except: pass
            l.append(v)
        return np.array(l)

    # Send a query to the instrument and get a response back.
    def instrumentQuery(self,q, *args, **kwargs):
        assert(self.inst)
        if self.quiet: return self.inst.query(q,*args,**kwargs)
        else:
            sys.stdout.write('\t'+q+'\t')
            sys.stdout.flush()
            response = self.inst.query(q,*args,**kwargs)
            sys.stdout.write(repr(response)+'\n')
            return response
            
    # Send a query to the instrument - no response.
    def instrumentWrite(self,q, *args, **kwargs):
        assert(self.inst)
        if not self.quiet: print '\t%s' % q
        self.inst.write(q,*args,**kwargs)
        return
            
    # Configure device settings based on subdriver choice
    def configure_device(self):
        if self.subdriver=='dg1000z':
            self.config['channel_names']=[]
            for n in range(1,3): self.config['channel_names'].extend(['CH%i_type' % n,\
                                                                    'CH%i_frequency' % n,\
                                                                    'CH%i_amplitude' % n,\
                                                                    'CH%i_offset' % n,\
                                                                    'CH%i_phase' % n,\
                                                                    'CH%i_pulse_width' % n,\
                                                                    'CH%i_burst' % n,\
                                                                    'CH%i_burst_delay' % n,\
                                                                    'CH%i_burst_source' % n])
            self.params['n_channels']=len(self.config['channel_names'])
            self.params['raw_units']=['']*self.params['n_channels']
            self.config['eng_units']=['']*self.params['n_channels']
            self.config['scale']=[1.]*self.params['n_channels']
            self.config['offset']=[0.]*self.params['n_channels']
            self.serialQuery = [':SOUR1:APPL?',':SOUR1FUNC:PULS:WIDT?',':SOUR1:BURS:STAT?',':SOUR1:BURS:TDEL?',':SOUR1:BURS:SOUR?',\
                                ':SOUR2:APPL?',':SOUR2FUNC:PULS:WIDT?',':SOUR2:BURS:STAT?',':SOUR2:BURS:TDEL?',':SOUR2:BURS:SOUR?']
        
        elif self.subdriver=='ds1000z':
            
            # Tell the scope to write waveforms in a known format
            self.instrumentWrite(":WAV:MODE RAW") # return what's in memory
            self.instrumentWrite(":WAV:FORM BYTE") # one byte per 8bit sample
            
            self.config['channel_names']=['Ch1','Ch2','Ch3','Ch4']
            self.params['raw_units']=['V','V','V','V']
            self.config['eng_units']=['V','V','V','V']
            self.config['scale']=[1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.]
            self.params['n_channels']=len(self.config['channel_names'])
            
            # Find out which channels are turned on, just acquire those.
            self.serialQuery=[]
            self.postQuery=':RUN'
            self.params['Active channels']=[]
            for nch in range(1,self.params['n_channels']+1):
                channel_active = int(self.instrumentQuery(":CHAN%1i:DISP?" % nch).strip())
                self.params['Active channels'].append(channel_active)
                if channel_active == 1:
                    self.serialQuery.append(":STOP,:WAV:SOUR %i,:WAV:DATA?" % nch)
                else:
                    self.serialQuery.append(None)
            
            # Get some parameters that don't change often
            self.params['Samples_per_sec'] = self.instrumentQuery(":ACQ:SRAT?")
            self.params['Seconds_per_div'] = self.instrumentQuery(":TIM:SCAL?")
            self.params['Bandwidth Limit'] = self.scope_channel_params("BWL")
            self.params['Coupling'] = self.scope_channel_params("COUP")
            self.params['Voltage Scale'] = self.scope_channel_params("SCAL")
            self.params['Inverted'] = self.scope_channel_params("INV")
            self.params['Vertical Offset'] = self.scope_channel_params("OFFS")
            self.params['Vertical Range'] = self.scope_channel_params("RANG")
        
            # Get some waveform parameters
            for n in range(1,self.params['n_channels']+1):
                self.instrumentWrite(":WAV:SOUR %1i" % n)
                time.sleep(0.01)
                self.params['Ch%i Waveform Parameters' % n] = self.instrumentQuery(":WAV:PRE?").split(',')
                time.sleep(0.01)

        elif self.subdriver == '33220a':
            
            self.instrumentWrite("SYST:BEEP") # beep the interface
            self.params['mode'] = self.ask('FUNC?') # Check the mode
            self.config['channel_names']=['frequency','amplitude','offset','duty cycle','pulse width']
            self.params['raw_units']=['Hz','V','V','','s']
            self.config['eng_units']=['Hz','V','V','','s']
            self.config['scale']=[1.,1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.,0.]
            self.params['n_channels']=len(self.config['channel_names'])
            if 'PULS' in self.params['mode']:
                self.serialQuery=['FREQ?','VOLT?','VOLT:OFFS?','FUNC:PULS:DCYC?', 'FUNC:PULS:WIDT?']
            elif 'SQU' in self.params['mode']:
                self.serialQuery=['FREQ?','VOLT?','VOLT:OFFS?','FUNC:SQU:DCYC?', None]
            else:
                self.serialQuery=['FREQ?','VOLT?','VOLT:OFFS?',None, None]
            
            # Now try to set the units more specifically
            self.params['raw_units'][1] = self.instrumentQuery("VOLT:UNIT?")
            self.config['eng_units'][1] = self.params['raw_units'][1]
            #self.params['raw_units'][4] = self.ask("UNIT:ANGL?")
            #self.config['eng_units'][4] = self.params['raw_units'][4]
            
            # Get some other parameters that won't change often.
            self.params['Trigger source'] = self.instrumentQuery("TRIG:SOUR?")

        else:
            print self.__doc__
            raise KeyError("Unknown device subdriver for pyvisa-py")
            return

    # Convert incoming value, which might be a string, to either a numpy array or a float
    def convert_to_array(self,data):
        if self.subdriver=='ds1000z':
            return np.array( struct.unpack(data,'<b'), dtype=np.uint8 ) # unpack scope waveform
            #return np.array(data) # simple list-to-array conversion
        else:
            return float(data)
        return None

    # Get values from device.
    # Standard query syntax is for comma-delimited return lists or single values, these are all concatenated.
    def get_values(self,delimiter=','):
        assert(self.inst)
        data=[]
        for q in self.serialQuery:
            if (q is None) or (q==''):
                data.append(None) # No query, empty response, i.e. for a disabled option
            else:
                try:
                    if self.subdriver=='ds1000z':
                        # Waveforms from scope.
                        if ',' in q: # Multiple commands ie setup or channel select
                            for qq in q.split(','): self.instrumentWrite(qq)
                        else:
                            self.instrumentWrite(q)
                        data.append(self.inst.read_raw())
                    else:
                        # Other simple data, floats and strings etc.
                        d=self.instrumentQuery(q).strip().strip('\"').strip('\'') # remove newlines, quotes, etc.
                        if delimiter in d: data.extend(d.split(delimiter)) # try to split on delimiter.
                        else: data.append(d)
                except:
                    data.append(None)
                    
            
        
        # Fill with None
        if len(data)<self.params['n_channels']:
            data.extend([None]*(self.params['n_channels']-len(data)))

        # Parse data, convert any floats or ints into numeric types.
        # convert array data to NumPy formatted float arrays.
        # Break out units into raw_units and eng_units
        self.lastValue=[]
        n=0
        for n in range(len(data)):
            try:
                if ' ' in data[n]:
                    d0=''.join(data[n].split(' ')[:-1])
                    d1=data[n].split(' ')[-1]
                else:
                    d0=data[n]
                    d1=''
                self.lastValue.append(self.convert_to_array(d0))
                self.params['raw_units'][n]=d1
                if self.config['eng_units'][n]=='':
                    self.config['eng_units'][n]=d1
            except ValueError:
                self.lastValue.append(d0)

        return

    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.inst)
            if self.inst is None: raise pyLabDataLoggerIOError
        except:
            print "Connection to the device is not open."

        # If first time or reset, get configuration (ie units)
        if not 'raw_units' in self.params.keys() or reset:
            
            # Set up device
            self.params['name']=self.instrumentQuery("*IDN?").replace(',',' ')
            if self.driver in self.name: self.name="%s %s" % (self.params['name'],self.params['resource'])
            self.configure_device()
        

        # Read values        
        self.get_values()

        # Run postQuery if exists (ie put the device in mode ready to accept next trigger/data)
        if hasattr('self', 'postQuery'):
            self.instrumentWrite(self.postQuery)

        # Generate scaled values. Convert non-numerics to NaNs
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            elif isinstance(v,basestring): lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


