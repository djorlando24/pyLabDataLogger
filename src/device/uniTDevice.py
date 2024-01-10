#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Uni-T USB HID device support
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2024 LTRAC
    @license GPL-3.0+
    @version 1.3.4
    @date 10/01/2024
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
class uniTDevice(device):
    """ Class providing support for Uni-T devices that use the WCH.CN USB HID chip.
        Sigrok should support them, but I found the support buggy.
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized uni-t"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        if 'quiet' in kwargs: self.quiet=kwargs['quiet']
        else: self.quiet=quiet
        self.driver = self.params['driver'].split('/')[1:]
        self.subdriver = self.driver[0].lower()
        
        if params is not {}: self.scan(quiet=self.quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        self.dev=None
        try:
            if self.subdriver=='ut32x':
                self.dev = usb.core.find(idVendor=0x1a86, idProduct=0xe008)
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        except:
            cprint( "Unable to find Uni-T USB HID device.", 'red', attrs=['bold'])
            return
        
        if self.dev is not None:
            self.activate(quiet=quiet)
        
        return

    # Establish connection to device.
    # Make sure the kernel will give up control of the USB device to us.
    def activate(self,quiet=False):
        
        if self.dev is None: raise pyLabDataLoggerIOError("Lost communication with Uni-T USB HID device.")
        
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
            if self.dev is None: raise pyLabDataLoggerIOError("Lost communication with Uni-T USB HID device.")
            
            # Apply subdriver-specific variable writes
            if subdriver=='ut32x':
                # There are no configurable options.
                pass
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        
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
        if not self.driverConnected: self.activate()
        else: cprint( "Error resetting %s: device is not detected" % self.name, 'red', attrs=['bold'])

    # Configure device based on what sub-driver is being used.
    # This is done when self.query(reset=True) is called, as at
    # this point we might need to poll the device to check a setting.
    def configure_device(self):
        if self.subdriver=='ut32x':
            self.name = "Uni-T or Tenma Thermometer"
            self.config['channel_names']=['Temperature','Timer','Timer String','InputChannel','Mode','Stored Record Count']
            self.params['raw_units']=['?','sec','mm:ss','','','']
            self.config['eng_units']=['?','sec','mm:ss','','','']
            self.config['scale']=[1.]*len(self.config['channel_names'])
            self.config['offset']=[0.]*len(self.config['channel_names'])
            self.params['n_channels']=len(self.config['channel_names'])
        else:
            raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        return

    # Send request for data and recieve data back over USB
    def get_values(self):
    
        if self.subdriver=='ut32x':
            
            #  Send the packets to tell the device to start transmitting on loop.
            timeout_ms=300
            bytes_to_read=512

            self.dev.ctrl_transfer(
                  0x21,  # REQUEST_TYPE_CLASS | RECIPIENT_INTERFACE | ENDPOINT_OUT
                  9,     # SET_REPORT
                  0x300, # "Vendor" Descriptor Type + 0 Descriptor Index
                  0,     # USB interface № 0
                  b'\x60\x09\x00\x00\x03' # the HID payload
            )

            s=b''
            self.dev.write(0x02, b"\x02\x5a\x00\x00\x00\x00\x00\x00", timeout_ms) # USBHID SET_REPORT Request
            s += self.dev.read(0x82, 8, timeout_ms) # USBHID SET_REPORT Response
            self.dev.write(0x02, b"\x01\x01\x00\x00\x00\x00\x00\x00", timeout_ms) # URB_INTERRUPT out

            # Loop to read streaming data back until we get an acceptable result or time runs out.
            meas_num=0
            mode=""; tempVal=np.nan; tempUnit=np.nan; nStored=np.nan; timeString=""; whichInput=""
            minutes=0; seconds=-1

            while ((meas_num<30) & np.isnan(tempVal)):

                # Read URB_INTERRUPT in
                s=b''
                s += self.dev.read(0x82, bytes_to_read, timeout_ms)
                
                i=0
                buf=b''
                if len(s)>=50:
                    if not b'\n' in s: break
                    i=s.index(b'\n')+7 # denotes end of last packet (in case first packet truncated)
                    while (i<len(s)):
                        # packet decoding
                        nbyte = s[i] - 0xf0 # calculate n bytes payload in this packet
                        if nbyte>0: buf += s[i+1:i+1+nbyte] # extract the data to buf
                        i+=8 # move to next packet
                        if b'\r\n' in buf: # escape on CRLF
                            buf = buf.split(b'\r\n')[0]
                            break

                    # debugging
                    if not self.quiet:
                        print("\tExtracted %i bytes payload from %i of %i raw bytes received" % (len(buf),i,len(s)))
                    
                    # decode payload
                    if len(buf)>=17:
                        mode, tempString, tempUnit, nStored, seconds, minutes, whichInput = struct.unpack('c4sc2sx2s2scxxx',buf[:17])
                        if mode == b'0': mode='memory'
                        elif mode == b'1': mode='realtime'
                        else: mode = mode.decode('ascii')
                        tempVal = float(tempString.decode('ascii').replace(':',''))*0.1
                        if tempUnit == b'1': tempUnit = 'degC'
                        elif tempUnit == b'2': tempUnit = 'degF'
                        elif tempUnit == b'3': tempUnit = 'K'
                        else: tempUnit = '?'
                        if whichInput == b'0': whichInput = 'T1'
                        elif whichInput == b'1': whichInput = 'T2'
                        elif whichInput == b'2': whichInput = 'T1-T2'
                        elif whichInput == b'3': whichInput = 'T1-T2'
                        else: whichInput='?'
                        nStored = int(nStored.decode('ascii'))
                        seconds = int(seconds.decode('ascii'))
                        minutes = int(minutes.decode('ascii'))

                meas_num+=1
            # End acq loop
            
            # Validate values
            if (tempVal<-99999) | (tempVal>99999): tempVal=np.nan
            if (nStored<0) | (nStored>99999): tmin=np.nan
            if (seconds<0) | (seconds>999999): tmin=np.nan
            if (minutes<0) | (minutes>999999): tmin=np.nan

            # Save values for recall
            #                ['Temperature','Timer','Timer String','InputChannel','Mode','Stored Record Count']
            self.lastValue = [ tempVal, minutes*60 + seconds, '%02i:%02i' % (minutes, seconds), whichInput, mode, nStored ]
            
            # Set units
            self.params['raw_units'][0] = tempUnit
            if (self.config['eng_units'][0] == "?"):
                self.config['eng_units'][0] = tempUnit
            
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
            elif isinstance(v,str): lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


