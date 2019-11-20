#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    lm-sensors device (monitoring computer temperatures and fan RPM)
 
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 20/11/2019
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
    import re, subprocess
except ImportError:
    print "Please install re, subprocess libraries"
    raise



########################################################################################################################
class lmsensorsDevice(device):
    """ Class providing support for lm-sensors in *nix systems.
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "lm-sensors"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.quiet = quiet
        self.params['driver'] = 'lm_sensors'
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        # check that sensors binary can be called and some chips exist
        if len(subprocess.check_output(['which sensors'])) < 1:
            print "lm-sensors not installed/available on this system"
        elif len(subprocess.check_output(['sensors']).strip()) < 1:
            print "lm-sensors detected no chips, try `sudo sensors-detect`"
        else: self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):

        # check which chips are present (this might change on a reset)
        self.config['channel_names']=[]
        self.params['raw_units']=[]
        self.config['eng_units']=[]

        output = [ line for line in subprocess.check_output(['sensors']).split('\n') if line != '' ]

        # add temperatures
        for j in range(len(output)):
            if 'Adapter:' in output[j]: adapter = ''.join(output[j].split(':')[1:])
            if '°C' in output[j]:
                self.config['channel_names'].append(adapter + ' ' + output[j].split(':')[0] + ' temp')
                self.params['raw_units'].append( '°C' )
                self.config['eng_units'].append( '°C' )
                if not self.quiet: print '\tDetected: %s' % self.config['channel_names'][-1]

        # add fan RPMs
        for j in range(len(output)):
            if 'Adapter:' in output[j]: adapter = ''.join(output[j].split(':')[1:])
            if 'RPM' in output[j]:
                self.config['channel_names'].append(adapter + ' ' + output[j].split(':')[0]+ ' RPM')
                self.params['raw_units'].append( 'RPM' )
                self.config['eng_units'].append( 'RPM' )
                if not self.quiet: print '\tDetected: %s' % self.config['channel_names'][-1]

        # Set up device
        self.params['n_channels']=len(self.config['channel_names'])
        self.config['scale']=[1.]*self.params['n_channels']
        self.config['offset']=[0.]*self.params['n_channels']       
        self.driverConnected=True
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):

        # ...

        self.driverConnected=False
        return

    # Apply configuration changes to the driver?
    def apply_config(self):
        #subdriver = self.params['driver'].split('/')[1:]
        try:
            assert(self.deviceClass)
            if self.deviceClass is None: raise pyLabDataLoggerIOError("Could not access device.")
            pass
        
        except ValueError:
            print "%s - Invalid setting requested" % self.name
            print "\t(V=",self.params['set_voltage'],"I=", self.params['set_current'],")"
        
        return

    # Update configuration
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


    def get_values(self):
        sensors = subprocess.check_output("sensors")

        # Temperatures
        #temperatures = {match[0]: float(match[1]) for match in re.findall("^(.*?)\:\s+\+?(.*?)°C", sensors, re.MULTILINE)}
        temperatures = [float(match[1]) for match in re.findall("^(.*?)\:\s+\+?(.*?)°C", sensors, re.MULTILINE)]

        # Fan speeds
        #rpms = {match[0]: float(match[1]) for match in re.findall("^(.*?)\:\s+\+?(.*?)RPM", sensors, re.MULTILINE)}
        rpms = [float(match[1]) for match in re.findall("^(.*?)\:\s+\+?(.*?)RPM", sensors, re.MULTILINE)]

        # SMART hard disks?
        #for d in self.lm_sensors_chips:
        #    output = subprocess.check_output(["smartctl", "-A", d])
        #    temperatures[d] = int(re.search("Temperature.*\s(\d+)\s*(?:\([\d\s]*\)|)$", output, re.MULTILINE).group(1))

        self.lastValue = list(temperatures) + list(rpms)

        return
   

    # Handle query for values
    def query(self, reset=False):

        
        # If first time or reset, get configuration (ie units)
        if not 'raw_units' in self.params.keys() or reset:
            driver = self.params['driver'].split('/')[1:]

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


