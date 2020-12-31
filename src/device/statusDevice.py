"""
    STATUS Instruments DIN rail USB signal amplifier support
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.0
    @date 20/12/2020
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
class statusDevice(device):
    """ Class providing support for STATUS Instruments DIN rail USB signal amplifiers.  (https://status.co.uk)
        - This presently only includes the SEM1600B, which is the only one I have access to for testing.
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized status device"
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
            if self.subdriver=='sem1600b':
                # find device
                self.dev = usb.core.find(idVendor=0x0403, idProduct=0xbab1)
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        except:
            cprint( "Unable to find Status USB device.", 'red', attrs=['bold'])
            return
        
        if self.dev is not None:
            self.activate(quiet=quiet)
        
        return

    # Establish connection to device.
    # Make sure the kernel will give up control of the USB device to us.
    def activate(self,quiet=False):
        
        if self.dev is None: raise pyLabDataLoggerIOError("Lost communication with Status USB device.")
        
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
            if self.dev is None: raise pyLabDataLoggerIOError("Lost communication with Status USB device.")
            
            # Apply subdriver-specific variable writes
            if subdriver=='sem1600b':
                # There are no configurable options.
                pass
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        
        except ValueError:
            cprint( "%s - Invalid setting requested" % self.name, 'red', attrs=['bold'])
            cprint( "\t(V="+self.params['set_voltage']+" I="+self.params['set_current']+")" , 'red')
        
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
        if self.subdriver=='sem1600b':
            self.name = "STATUS SEM1600B Load Cel Amplifier"
            #Raw=%f, Input=%f, Filtered Input=%f, Process=%f, PercentOutput=%f, OutputSignal
            self.config['channel_names']=['Raw','Input','Filtered_Input','Process_Output','Percent_Output','Output_Signal']
            self.params['raw_units']=['cts','mV','mV','PV','%','mA']
            self.config['eng_units']=['cts','mV','mV','PV','%','mA']
            self.config['scale']=[1.]*len(self.config['channel_names'])
            self.config['offset']=[0.]*len(self.config['channel_names'])
            self.params['n_channels']=len(self.config['channel_names'])
        else:
            raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        return

    # Send request for data and recieve data back over USB
    def get_values(self):
    
        if self.subdriver=='sem1600b':

            # Send control bytes
            assert self.dev.ctrl_transfer(0x40,0,0x0001,0x0000,8,timeout=100) == 8
            time.sleep(.01)
            assert self.dev.ctrl_transfer(0x40,3,0x809c,0x0000,8,timeout=100) == 8
            time.sleep(.01)
            assert self.dev.ctrl_transfer(0x40,4,0x0008,0x0000,8,timeout=100) == 8
            time.sleep(.01)
            assert self.dev.ctrl_transfer(0x40,2,0x0000,0x0000,8,timeout=100) == 8
            time.sleep(.01)
            assert self.dev.ctrl_transfer(0x40,9,0x0003,0x0000,8,timeout=100) == 8
            time.sleep(.01)

            # Send bulk URB_OUT to initiate data transfer
            self.dev.write(0x02, "\x01\x04\x28\x00\x00\x98\xf8\x00", 100)
            time.sleep(.05)

            # Read response
            s=''
            empty_responses=0
            while (len(s)<128) or (empty_responses<50):
                try:
                    buf = array.array('B','')
                    buf = self.dev.read(0x81, 128, timeout=100)
                    s+=''.join(struct.unpack('%ic' % len(buf),buf)) #buf.tostring()
                    if buf == array.array('B',[1,96]): empty_responses+=1 # This is an empty return string
                    else: empty_responses=0
                except usb.core.USBError as e:
                    break
    
            if len(s) < 25:
                cprint( "\tStatus SEM1600B communication failed.", 'red', attrs=['bold'])
                return
            
            # Extraction of values. Little endian floats are buried inside the byte string.
            raw = struct.unpack('<f',s[ 5: 5+4])[0]
            inp = struct.unpack('<f',s[ 9: 9+4])[0]
            pro = struct.unpack('<f',s[13:13+4])[0]
            per = struct.unpack('<f',s[17:17+4])[0]
            ous = struct.unpack('<f',s[21:21+4])[0]
            flt = struct.unpack('<f',s[25:25+4])[0]
            
            # Validate values
            #if (raw<-9) | (emis>1.): emis=np.nan
            #if (tmin<-999) | (tmin>999): tmin=np.nan
            #if (tmax<-999) | (tmax>999): tmin=np.nan
            #f (tcur<-999) | (tcur>999): tmin=np.nan

            # Save values for recall
            #['Raw','Input','Filtered_Input','Process_Output','Percent_Output','Output_Signal']
            self.lastValue = [ raw, inp, flt, pro, per, ous ]
            
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


