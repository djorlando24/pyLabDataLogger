#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Omega Smart Probe Layer N Modbus Compatible Devices
    - currently supports USB access via TTY
    
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
"""

from .device import device
from .device import pyLabDataLoggerIOError
import numpy as np
import datetime, time, serial, os
from termcolor import cprint

try:
    import omegasensor
except ImportError:
    cprint( "Please install omega-smartsensor-python", 'red', attrs=['bold'])
    cprint( "https://github.com/omegaengineering/omega-smartsensor-python" ,'red')
    raise

########################################################################################################################
class omegaSmartProbeDevice(device):
    """ Class providing support for Omega Layer N Modbus Compatible Smart Probes.
    
        By default we assume that the port can be found in /dev/tty*
        However this can be overridden by passing 'port' directly
        in the params dict.
        
        The hardware connected to the device will be autodetected and all
        channels saved. The MODBUS address of the device can be passed via
        the params dict as MODBUS_ADDR, otherwise it is assumed to be 1.
        
        You will need one instance of the omegaSmartProbeDevice class per device
        on the bus, if there is more than one.
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet
        
        if 'debugMode' in kwargs: self.debugMode = kwargs['debugMode']
        else: self.debugMode=False
        
        self.driver = self.params['driver'].split('/')[1:]
        
        if params is not {}: self.scan(quiet=self.quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        self.port = None
        if override_params is not None: self.params = override_params
        
        # Find the tty associated with the serial port
        if 'tty' in self.params.keys():
            self.port = self.params['tty']
        elif 'port' in self.params.keys():
            self.port = self.params['port']
        elif 'pid' in self.params.keys() and 'vid' in self.params.keys(): # USB serial
            
            # This will find all serial ports available to pySerial.
            # We hope the USB device scanned in usbDevice.py can be found here.
            # We need to find an exact match - there may be multiple generic devices.
            from serial.tools import list_ports
            
            # This subroutine will check for matching bus-address locations
            # to identify a particular device even if VID and PID are generic.
            def locationMatch(serialport):
                # Check for bus and port match (for multiple generic serial adapters...)
                if ('port_numbers' in self.params) and ('bus' in self.params) and ('location' in dir(serialport)):
                    search_location = '%i-%s' % (self.params['bus'],'.'.join(['%i'% nn for nn in self.params['port_numbers']]))
                    if (search_location == serialport.location):
                        if not self.quiet: cprint( '\tVID:PID match- location %s == %s' % (search_location,\
                                                  serialport.location) , 'green')
                        return True
                    elif ((':' not in search_location) and (':' in serialport.location)): # if '2-1' doesn't match '2-1:1.0' for example.
                        if search_location in serialport.location:
                            if not self.quiet: cprint( '\tVID:PID match- location %s == %s' % (search_location,\
                                                  serialport.location) , 'green')
                            return True
                    else:
                        if not self.quiet: cprint( '\tVID:PID match but location %s does not match %s' % (repr(search_location),\
                                                repr(serialport.location)), 'yellow' )
                        return False
                else:
                    # If the feature is unsupported, assume first device is the real one! We can't check.
                    return True
                    
            
            #####################################################################################################################
            # scan all serial ports the OS can see
            for serialport in list_ports.comports():
                
                # Not all versions of pyserial have the list_ports_common module!		
                if 'list_ports_common' in dir(serial.tools):
                    objtype=serial.tools.list_ports_common.ListPortInfo
                else:
                    objtype=None

                # if serialport returns a ListPortInfo object
                if objtype is not None and isinstance(serialport,objtype):
                    
                    thevid = serialport.vid
                    thepid = serialport.pid
                    if thevid==self.params['vid'] and thepid==self.params['pid'] and locationMatch(serialport):
                        self.params['tty']=serialport.device
                        self.port=serialport.device
            
                # if the returned device is a list, tuple or dictionary
                elif len(serialport)>1:

		            # Some versions return a dictionary, some return a tuple with the VID:PID in the last string.
                    if 'VID:PID' in serialport[-1]: # tuple or list
                        thename = serialport[0]
                        # Sometimes serialport[-1] will contain "USB VID:PID=0x0000:0x0000" and
                        # sometimes extra data will follow after, i.e. "USB VID:PID=1234:5678 SERIAL=90ab".
                        if not self.quiet: print( '\t'+str(serialport[-1])) # report to terminal, useful for debugging.
                        vididx = serialport[-1].upper().index('PID')
                        if vididx <= 0: raise IndexError("Can't interpret USB VID:PID information!")
                        vidpid = serialport[-1][vididx+4:vididx+13] # take fixed set of chars after 'PID='
                        thevid,thepid = [ int(val,16) for val in vidpid.split(':')]
                        if thevid==self.params['vid'] and thepid==self.params['pid'] and locationMatch(serialport):
                            
                            if not self.quiet: print( '\t'+str(serialport))
                            if thename is not None:
                                self.port = thename # Linux
                            else:
                                self.port = serialport.device # MacOS
                            if not self.tty_prefix in self.port: self.port = self.tty_prefix + self.port
                            self.params['tty']=self.port

                    elif 'vid' in dir(serialport): # dictionary
                        if serialport.vid==self.params['vid'] and serialport.pid==self.params['pid'] and locationMatch(serialport):
                            # Vid/Pid matching
                            if not self.quiet: print( '\t'+str(serialport.hwid)+' '+str(serialport.name))
                            if serialport.name is not None:
                                self.port = serialport.name # Linux
                            else:
                                self.port = serialport.device # MacOS
                            if not self.tty_prefix in self.port: self.port = self.tty_prefix + self.port
                            self.params['tty']=self.port

                # List or dict with only one entry.
                elif len(list_ports.comports())==1: # only one found, use as default
                    self.port = serialport[0]
                    if not self.tty_prefix in self.port: self.port = self.tty_prefix + self.port
                    self.params['tty']=self.port

                if 'tty' in self.params:
                    if os.path.exists(self.params['tty']): break
            #####################################################################################################################
        
        if self.port is None:
            cprint( "\tUnable to connect to serial port - port unknown.", 'red', attrs=['bold'])
            cprint( "\tYou may need to install a specific USB-to-Serial driver.",'red')
            cprint( "\tfound non-matching ports:", 'red')
            cprint( list_ports.comports()[0], 'red')
            raise pyLabDataLoggerIOError("Serial port driver missing")
        
        else: self.activate(quiet=self.quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
        
        # default modbus address = 1
        if not 'MODBUS_ADDR' in self.params:
            self.params['MODBUS_ADDR']=1
        
        self.bus = omegasensor.BusModbus(self.port, self.params['MODBUS_ADDR'])
        self.dev = omegasensor.Smartsensor(self.bus)
        
        self.driverConnected=True
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        del self.dev
        del self.bus
        self.driverConnected=False
        return

    # Apply configuration changes to the driver
    def apply_config(self):
        try:
            assert(self.dev)
            if self.deviceClass is None: raise pyLabDataLoggerIOError("Could not access device.")
            
            #...
            
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
        if self.driverConnected: self.activate()
        else: cprint( "Error resetting %s: device is not detected" % self.name, 'red', attrs=['bold'])

    

    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.dev)
            if self.dev is None: raise pyLabDataLoggerIOError
        except:
            cprint( "Connection to the device is not open.", 'red', attrs=['bold'])

        # If first time or reset, get configuration (ie units)
        if not 'raw_units' in self.params.keys() or reset:
            
            
            self.dev.soft_reset()
            self.dev.preset_config()    
            ''' #Debugging
            for k in omegasensor.R:
                try:
                    X = self.dev.read(eval("omegasensor.R.%s" % k.value))
                    if not 'omegasensor' in str(type(X)):
                        print("%s: %s" % (k.value, repr(X) ))
                    else:
                        print("%s: %s" % (k.value, dir(X)  ))
                except AttributeError: 
                    pass
            '''
            
            self.name = "Omega Smart Probe %s %0i" % (self.dev.read(omegasensor.R.DEVICE_NAME_LIST)[1:],self.params['MODBUS_ADDR'])
            self.params['Firmware Version'] = "0x%08x" % self.dev.read(omegasensor.R.FIRMARE_VERSION)
            self.params['Hardware Version'] = "0x%08x" % self.dev.read(omegasensor.R.HARDWARE_VERSION)
            self.params['Core Version'] = "0x%08x" % self.dev.read(omegasensor.R.CORE_VERSION)
            self.params['Long Device ID'] = "0x%08x" % self.dev.read(omegasensor.R.LONG_DEVICE_ID)
            self.params['Device ID'] = "0x%08x" % self.dev.read(omegasensor.R.DEVICE_ID)
            self.params['Device Name'] = self.dev.read(omegasensor.R.DEVICE_NAME)
            self.params['n_channels'] = self.dev.read(omegasensor.R.IO_COUNT).sensors
            self.config['channel_names']=[self.dev.read(omegasensor.R.SENSOR_0_DESCRIPTOR).meas_type.name,\
                                          self.dev.read(omegasensor.R.SENSOR_1_DESCRIPTOR).meas_type.name,\
                                          self.dev.read(omegasensor.R.SENSOR_2_DESCRIPTOR).meas_type.name,\
                                          self.dev.read(omegasensor.R.SENSOR_3_DESCRIPTOR).meas_type.name]
            self.config['channel_names'] = self.config['channel_names'][:self.params['n_channels']]
            self.params['raw_units']=[self.dev.sensor_unit(i).strip() for i in range(self.params['n_channels'])]
            self.config['eng_units']=[self.dev.sensor_unit(i).strip() for i in range(self.params['n_channels'])]
            self.config['scale']=[1.]*self.params['n_channels']
            self.config['offset']=[0.]*self.params['n_channels']
            
        # Read values        
        self.lastValue = [ self.dev.sensor_reading(i) for i in range(self.params['n_channels']) ]

        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


