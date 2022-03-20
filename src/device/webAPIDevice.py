"""
    Device class for web-based API calls via HTTPS (IoT devices)   
 
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2.4
    @date 20/03/2022
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
	
	Initialisation requires a URL parameter passed via the constructor or in the params dictionary.
        The 'format' parameter is 'json' by default. In future 'xml' could be supported as well.    

    """

    def __init__(self,params={},url=None,format='json',quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized web API Device"
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

    # Detect if URL is valid
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
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
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
            for v in d: print(v)
        else:
            raise pyLabDataLoggerIOError("Sorry, I can't understand data from that device - please edit webAPIDevice.py")
        
        return
