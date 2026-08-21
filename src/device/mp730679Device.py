#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Wrapper class for Multicomp Pro mp730679, also Uni-T ut16e+
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 21/02/2026

    Multiphase Flow Laboratory
    Monash University, Australia
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or

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
import datetime, time
from termcolor import cprint

from .ut61eplus.ut61eplus import UT61EPLUS

########################################################################################################################
class mp730679Device(device):
    """ Support for Multicomp Pro MP730679 or Uni-T UT61e+
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet
        
        if 'debugMode' in kwargs: self.debugMode = kwargs['debugMode']
        else: self.debugMode=False
            
        self.name = "MP730679 Multimeter"
        self.config['channel_names']=['value','display','display_decimal','mode','range','overload','status','unit','display_unit']
        self.params['raw_units']=['?','?','?','','','','','',''] # will be updated on 1st read
        self.config['eng_units']=['?','?','?','','','','','',''] # will be refreshed regularly.
        self.config['scale']=[1.]*len(self.config['channel_names'])
        self.config['offset']=[0.]*len(self.config['channel_names'])
        self.params['n_channels']=len(self.config['channel_names'])
        
        if params is not {}: self.scan(quiet=self.quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        if override_params is not None: self.params = override_params
        self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
        try:
            self.dev = UT61EPLUS()
            self.driverConnected=True
            # Make first query to get units, description, etc.
            self.query(reset=True)
            if not quiet: self.pprint()
        except OSError:
            cprint("HID USB device: You may need to run the program as root/administrator",'red', attrs=['bold'])
            self.driverConnected=False
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        del self.dev
        self.driverConnected=False
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        pass
        return

    # Update configuration (ie change sample rate or number of samples)
    def update_config(self,config_keys={}):
        pass
        return

    def updateTimestamp(self):
        self.lastValueTimestamp = datetime.datetime.now()

    # Re-establish connection to device.
    def reset(self):
        self.deactivate()
        self.scan()
        if self.driverConnected: self.activate()
        else: cprint( "Error resetting %s: device is not detected" % self.name, 'red', attrs=['bold'])

    # Handle query for values
    def query(self, reset=False):
        
        try:
            assert self.dev
            measurement = self.dev.takeMeasurement()
            if not measurement:
                self.lastValue=[np.nan]*self.params['n_channels']
                self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
                return self.lastValue
        except AttributeError:
            cprint("MP730679 unable to connect.",'red')
            self.lastValue=[np.nan]*self.params['n_channels']
            self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            return self.lastValue
        
        
        # If first time or reset, get measurement units
        if not 'raw_units' in self.params.keys() or reset:
            #self.config['channel_names']=['value','display','display_decimal','mode','range','overload','status']
            self.params['raw_units']=[measurement.unit, measurement.display_unit, measurement.display_unit,'','','','','','']
        
        # Every time, update current engineering units in case they change
        self.config['eng_units']=[measurement.unit, measurement.display_unit, measurement.display_unit,'','','','','','']
        
        # Put in result
        statusText=''
        if measurement.isDC: statusText+='DC '
        if measurement.isAuto: statusText+='Auto '
        if measurement.isMaxPeak: statusText+='max-peak '
        elif measurement.isMax: statusText+='max '
        elif measurement.isMinPeak: statusText+='min-peak '
        elif measurement.isMin: statusText+='min '
        if measurement.isHold: statusText+='HOLD '
        if measurement.isRel: statusText+='rel '
        if measurement.hasHVWarning: statusText+='HIGH-VOLTAGE-WARNING '
        
        if measurement.hasBatteryWarning: statusText+='LOW-BATT'
        self.lastValue=[float(measurement.value),float(measurement.display),float(measurement.display_decimal),\
                        measurement.mode,measurement.range,int(measurement.overload),\
                        statusText.strip(),measurement.unit,measurement.display_unit]
        
        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue:
            if v is None: lastValueSanitized.append(np.nan)
            elif type(v)==str: lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


