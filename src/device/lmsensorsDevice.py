#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    lm-sensors device (monitoring computer temperatures and fan RPM)
 
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
    
    Updated 04/02/22 with improved channel name and python3 string handling.
"""

from .device import device
from .device import pyLabDataLoggerIOError
import numpy as np
import datetime, time
from termcolor import cprint

try:
    import re, subprocess
except ImportError:
    cprint( "Please install re, subprocess libraries", 'red', attrs=['bold'])
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
        self.lastValue = [0] # Last known value (for logging)
        self.lastScaled = [0]
        self.lastValueTimestamp = None # Time when last value was obtained
        self.quiet = quiet
        self.params['driver'] = 'lm_sensors'
        self.params['n_channels']=1
        self.config['channel_names']=['NULL']
        self.params['raw_units']=['']
        self.config['eng_units']=['']
        self.config['scale']=[1.]
        self.config['offset']=[0.]
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        # check that sensors binary can be called and some chips exist
        try:
            if len(subprocess.check_output(['which','sensors'])) < 1:
                cprint( "lm-sensors not installed/available on this system", 'red', attrs=['bold'])
            elif len(subprocess.check_output(['sensors']).strip()) < 1:
                cprint( "lm-sensors detected no chips, try `sudo sensors-detect`", 'red', attrs=['bold'])
            else: self.activate(quiet=quiet)
        except OSError as e:
            cprint( "lm-sensors is not installed/available on this system:", 'red', attrs=['bold'])
            cprint(e, 'red')
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):

        # check which chips are present (this might change on a reset)
        self.config['channel_names']=[]
        self.params['raw_units']=[]
        self.config['eng_units']=[]
        self.config['scale']=[]
        self.config['offset']=[]
        self.config['adapter']=[]
        
        try:
            output = [ line for line in subprocess.check_output(['sensors']).split(b'\n') if line != '' ]
        except OSError:
            raise pyLabDataLoggerIOError("lm-sensors not available")
        
        cprint("Loading lmsensors device...",'green')
        
        # add temperatures
        for j in range(len(output)):
            if b'Adapter:' in output[j]: adapter = ''.join(output[j].decode('utf-8').split(':')[1:])
            if '°C' in output[j].decode('utf-8') and b':' in output[j]:
                #chname = adapter + ' ' + output[j].decode('utf-8').split(':')[0] + ' temp' # long name
                chname = output[j].decode('utf-8').split(':')[0] # shorter name
                self.config['channel_names'].append(self.make_unique_chname(chname))
                self.params['raw_units'].append( '°C' )
                self.config['eng_units'].append( '°C' )
                self.config['adapter'].append(adapter)
                if not self.quiet: print('\tDetected: %s' % self.config['channel_names'][-1])
                
        # add fan RPMs
        for j in range(len(output)):
            if b'Adapter:' in output[j]: adapter = ''.join(output[j].decode('utf-8').split(':')[1:])
            if b'RPM' in output[j] and b':' in output[j]:
                #chname = adapter + ' ' + output[j].decode('utf-8').split(':')[0] + ' RPM' # long name
                chname = output[j].decode('utf-8').split(':')[0] # shorter name
                self.config['channel_names'].append(self.make_unique_chname(chname))
                self.params['raw_units'].append( 'RPM' )
                self.config['eng_units'].append( 'RPM' )
                self.config['adapter'].append(adapter)
                if not self.quiet: print('\tDetected: %s' % self.config['channel_names'][-1])

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
            cprint( "%s - Invalid setting requested" % self.name, 'red', attrs=['bold'])
        
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
        else: cprint( "Error resetting %s: device is not detected" % self.name, 'red', attrs=['bold'])


    def get_values(self):
        try:
            sensors = subprocess.check_output("sensors")
        except:
            self.lastValue = [None]*self.params['n_channels']
            raise pyLabDataLoggerIOError("lm-sensors not available")
        
        # Temperatures
        #temperatures = {match[0]: float(match[1]) for match in re.findall("^(.*?)\:\s+\+?(.*?)°C", sensors, re.MULTILINE)}
        temperatures = [float(match[1]) for match in re.findall("^(.*?)\:\s+\+?(.*?)°C", sensors.decode('utf-8'), re.MULTILINE)]

        # Fan speeds
        #rpms = {match[0]: float(match[1]) for match in re.findall("^(.*?)\:\s+\+?(.*?)RPM", sensors, re.MULTILINE)}
        rpms = [float(match[1]) for match in re.findall("^(.*?)\:\s+\+?(.*?)RPM", sensors.decode('utf-8'), re.MULTILINE)]

        # SMART hard disks?
        #for d in self.lm_sensors_chips:
        #    output = subprocess.check_output(["smartctl", "-A", d])
        #    temperatures[d] = int(re.search("Temperature.*\s(\d+)\s*(?:\([\d\s]*\)|)$", output, re.MULTILINE).group(1))

        self.lastValue = list(temperatures) + list(rpms)

        return
   

    # Handle query for values
    def query(self, reset=False):

        if not self.driverConnected: return pyLabDataLoggerIOError("lm-sensors not available") 
      

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

    # Ensure channel name is unqiue, as lm-sensors can report many identical variable names.
    def make_unique_chname(self,chname):
        if chname in self.config['channel_names']:
            i=1
            while chname+' %i' % i in self.config['channel_names']: 
                i+=1
            return chname + ' %i' % i
        return chname
                        


