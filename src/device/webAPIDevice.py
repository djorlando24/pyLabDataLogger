#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Device class for web-based API calls via HTTPS (IoT devices)   
 
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2025 D.Duke
    @license GPL-3.0+
    @version 1.4.0
    @date 08/06/25

    Multiphase Flow Laboratory
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
import datetime, time
from termcolor import cprint

try:
    import json, requests
except ImportError:
    cprint( "Please install json and requests libraries", 'red', attrs=['bold'])
    raise

########################################################################################################################
class webAPIDevice(device):
    """ Class providing support for HTTPS Web API Devices.
	
	Initialisation requires the following parameters passed via the constructor or in the params dictionary.
        
                url (string)    : specify API URL including any API key required
                format (string) : 'json' [default] or 'xml'
                name (string)   : name of device - default will use data from the server to guess

        The 'format' parameter is 'json' by default. In future 'xml' could be supported as well.    

    """

    def __init__(self,params={},url=None,format='json',name=None,quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet
        
        if 'debugMode' in kwargs: self.debugMode = kwargs['debugMode']
        else: self.debugMode=False
        
        #self.driver = self.params['driver'].split('/')[1:]
        #self.subdriver = self.driver[0].lower()
        
        if 'format' in params:
            self.fmt=params['format']
        else:
            self.fmt=format

        if 'name' in params:
            self.name=params['name']
        else:
            self.name=name

        self.url=None
        if url is None:
            for k in ['url','URL','Url']: 
                if k in params:     
                    self.url = params[k]
        else:
            self.url = url

        if self.url is None:
            raise pyLabDataLoggerIOError("No URL specified for web API call.")
            return
        
        if params is not {}: self.scan(quiet=self.quiet)
        
        return

    def scan(self,override_params=None,quiet=False):
        if override_params is not None: self.params = override_params
        self.activate(quiet=quiet)
        return

    # Establish connection
    def activate(self,quiet=False):
        
        # Nothing to do here, since we already called the API ok.
        self.driverConnected=True
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        # Nothing to do.
        self.driverConnected=False
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        # No config changes can be applied here. 
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
        else: cprint( "Error resetting %s: device is not detected" % self.name, 'red', attrs=['bold'])

    # Handle query for values
    def query(self, reset=False):

        # Get data from server
        data={}
        if self.fmt == 'json': # JSON format
            u = requests.get(self.url)
            data = json.loads(u.text)
        else:
            raise pyLabDataLoggerIOError("Error: data format %s not supported - please contact developer" % self.fmt)
       
        self.convert_data(data,reset)
 
        # Generate scaled values. Convert non-numerics to NaN
        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue:
            if v is None: lastValueSanitized.append(np.nan)
            #elif isinstance(v, basestring): lastValueSanitized.append(np.nan)  # python2
            elif isinstance(v, str): lastValueSanitized.append(np.nan)  # python3
            elif isinstance(v, bytes): lastValueSanitized.append(np.nan)  # python3
            else:    lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        
        self.updateTimestamp()
        return self.lastValue

    # Process the data based on what kind of device we are talking to.
    # If 'reset' is True then we will need to define all the params and config attributes.
    def convert_data(self, data, reset=False):

        if 'kaiterra' in self.url.lower():
            # KAITERRA device
            self.config['id'] = data['id']
            d=data['data']

            if reset:
                if self.name is None: self.name = 'Kaiterra Device %s' % self.config['id']
                self.params['n_channels']=len(d)+1
                self.config['channel_names']=[v['param'] for v in d]
                self.config['scale']=[1.]*self.params['n_channels']
                self.config['offset']=[0.]*self.params['n_channels']
                self.params['raw_units']=[v['units'] for v in d]
                self.config['eng_units']=[v['units'] for v in d]
                self.config['span']=','.join(str([v['span'] for v in d]))
            
                self.config['channel_names'].append('timestamp') # RFC339 time stamp
                self.params['raw_units'].append('')
                self.config['eng_units'].append('')

            self.lastValue = [float(v['points'][0]['value']) for v in d]
            self.lastValue.append(d[0]['points'][0]['ts']) # use first var's timestamp
                 
        else:
            raise pyLabDataLoggerIOError("Sorry, I can't understand data from that device - please edit webAPIDevice.py")
        
        return
