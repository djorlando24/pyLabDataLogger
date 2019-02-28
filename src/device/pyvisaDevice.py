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
import datetime, time

try:
    import visa
except ImportError:
    print "Please install pyvisa-py"
    raise

########################################################################################################################
class pyvisaDevice(device):
    """ Class providing support for pyVISA-py devices.
    """

    def __init__(self,params={},quiet=False,**kwargs):
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
            self.rm = visa.ResourceManager('@py')
        else:
            raise ValueError("Unknown Driver. Use 'pyvisa/X' for device X.")

        assert(self.rm)
        
        if not 'resource' in self.params:
            print "pyVISA-py: Please specify a resource. Possible resources include but not limited to:"
            print self.rm.list_resources()
            return
        
        self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
    
        self.inst = self.rm.open_resource(self.params['resource'])
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
            else:
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
        else:
            raise KeyError("Unknown device subdriver for pyvisa-py")
            return

    # Get values from device.
    # Standard query syntax is for comma-delimited return lists or single values, these are all concatenated.
    def get_values(self,delimiter=','):
        assert(self.inst)
        data=[]
        for q in self.serialQuery:
            try:
                d=self.inst.query(q).strip().strip('\"').strip('\'') # remove newlines, quotes, etc.
                if delimiter in d: data.extend(d.split(delimiter)) # try to split on delimiter.
                else: data.append(d)
            except:
                self.lastValue.append(None)
        
        # Fill with None
        if len(data)<self.params['n_channels']:
            data.extend([None]*(self.params['n_channels']-len(data)))

        # Parse data, convert any floats or ints into numeric types
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
                self.lastValue.append(float(d0))
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
            self.params['name']=self.inst.query("*IDN?")
            if self.driver in self.name: "pyVISA-py device %s" % self.params['name']
            self.configure_device()
        

        # Read values        
        self.get_values()

        # Generate scaled values. Convert non-numerics to NaNs
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            elif isinstance(v,basestring): lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


