"""
    Fluke USB device support
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2
    @date 19/01/2022
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
import datetime, time, struct, array
from termcolor import cprint

try:
    import usb.core
    import usb.util
except ImportError:
    cprint( "Please install pyUSB library", 'red', attrs=['bold'])
    raise

########################################################################################################################
class flukeusbDevice(device):
    """ Class providing support for Fluke USB devices that normally work with the FlukeView Forms software.
        - Currently this includes only the Fluke 568 thermometer - that's all I have access to.
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized flukeusb"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        
        self.driver = self.params['driver'].split('/')[1:]
        self.subdriver = self.driver[0].lower()
        
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        self.dev=None
        try:
            if self.subdriver=='568':
                # find device
                # ID 0f7e:9002 Fluke Corp.
                self.dev = usb.core.find(idVendor=0x0f7e, idProduct=0x9002)
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        except:
            cprint( "Unable to find Fluke USB device.", 'red', attrs=['bold'])
            return
        
        if self.dev is not None:
            self.activate(quiet=quiet)
        
        return

    # Establish connection to device.
    # Make sure the kernel will give up control of the USB device to us.
    def activate(self,quiet=False):
        
        if self.dev is None: raise pyLabDataLoggerIOError("Lost communication with Fluke USB device.")
        
        # Make sure OS kernel isn't hogging the device
        for cfg in self.dev:
            for intf in cfg:
                if self.dev.is_kernel_driver_active(intf.bInterfaceNumber):
                    try:
                        self.dev.detach_kernel_driver(intf.bInterfaceNumber)
                    except usb.core.USBError as e:
                        raise pyLabDataLoggerIOError("Could not detatch kernel driver from interface({0}):{1}".format(intf.bInterfaceNumber, str(e)))

        # Claim the interface 0 of the device
        usb.util.claim_interface(self.dev, 0)

        self.driverConnected=True
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        del self.dev
        self.dev = None
        self.driverConnected=False
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        try:
            assert(self.dev)
            if self.dev is None: raise pyLabDataLoggerIOError("Lost communication with Fluke USB device.")
            
            # Apply subdriver-specific variable writes
            if subdriver=='568':
                # There are no configurable options.
                pass
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        
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
        if not self.driverConnected: self.activate()
        else: cprint( "Error resetting %s: device is not detected" % self.name, 'red', attrs=['bold'])

    # Configure device based on what sub-driver is being used.
    # This is done when self.query(reset=True) is called, as at
    # this point we might need to poll the device to check a setting.
    def configure_device(self):
        if self.subdriver=='568':
            self.name = "Fluke 568 IR thermometer"
            self.config['channel_names']=['IR Temp','IR min','IR max','IR delta','thermocouple','emissivity','measurementNumber']
            self.params['raw_units']=['C','C','C','C','C','','']
            self.config['eng_units']=['C','C','C','C','C','','']
            self.config['scale']=[1.]*len(self.config['channel_names'])
            self.config['offset']=[0.]*len(self.config['channel_names'])
            self.params['n_channels']=len(self.config['channel_names'])
            self.params['device ID']=''
            self.params['units code']=1
        else:
            raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        return

    # Send request for data and recieve data back over USB
    def get_values(self):
    
        if self.subdriver=='568':
            # Send control bytes
            request = b'\x81\x02\x05\x00\x00\x00\x00\x00'
            assert self.dev.ctrl_transfer(0x21,0x09,0x0200,0x0000,request)==len(request)

            # Read response
            s=b""
            while len(s)<64:
                try:
                    buf = array.array('B',b'')
                    buf = self.dev.read(0x81, 64, timeout=100)
                    s+=b"".join(struct.unpack('%ic' % len(buf),buf))
                except usb.core.USBError as e:
                    break
    
            if len(s) < 64:
                cprint( "\tFluke 568 communication failed.", 'red', attrs=['bold'])
                return
            
            # Extraction of values. Little endian floats are buried inside the byte string.
            # We'll ignore the checksum for now.
            emis = struct.unpack('<f',s[25:25+4])[0]
            tmin = struct.unpack('<f',s[36:36+4])[0]
            tcur = struct.unpack('<f',s[48:48+4])[0]
            tmax = struct.unpack('<f',s[42:42+4])[0]
            delt = struct.unpack('<f',s[54:54+4])[0]
            meas_id = struct.unpack('<L',s[6:6+4])[0]
            # Thermocouple, if present.
            if s[29:30]==b' ': ttrm = struct.unpack('<f',s[31:31+4])[0]
            else: ttrm=np.nan
            # Device ID, if initialising first time
            if self.params['device ID']=='':
                self.params['device ID']= repr(s[:3]).replace('\\x','')
            
            # Validate values
            if (emis<0.) | (emis>1.): emis=np.nan
            if (tmin<-999) | (tmin>999): tmin=np.nan
            if (tmax<-999) | (tmax>999): tmin=np.nan
            if (tcur<-999) | (tcur>999): tmin=np.nan

            # Save values for recall
            self.lastValue = [ tcur, tmin, tmax, delt, ttrm, emis, meas_id ]

            # Check if units of measurement changed
            flags = struct.unpack('8B',s[56:64])
            if flags[4] != self.params['units code']:
                self.params['units code'] = flags[4]
                for nn in range(5):
                    if flags[4] == 1:
                        self.params['raw_units'][nn] = 'C'
                    elif flags[4] == 2:
                        self.params['raw_units'][nn] = 'F'
                    else:
                        self.params['raw_units'][nn] = ''
                    # Update engineering units if there's no preset scaling.
                    if (self.config['scale'][nn] == 1.) & (self.config['offset'][nn] == 0.):
                        self.config['eng_units'][nn] = self.params['raw_units'][nn]
            
        else:
            raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        
        return


    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.dev)
            if self.dev is None: raise pyLabDataLoggerIOError
        except:
            cprint( "\tConnection to the device is not open.", 'red', attrs=['bold'])

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
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


