#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    pyAPT device class - Thorlabs stepper motors
    
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
import datetime, time
from termcolor import cprint

try:
    import pylibftdi
    import pyAPT
except ImportError:
    cprint( "Please install pyAPT and pylibftdi", 'red', attrs=['bold'])
    exit()

try:
    import usb.core
except ImportError:
    cprint( "Please install pyUSB", 'red', attrs=['bold'])
    raise

########################################################################################################################
class pyAPTDevice(device):
    """
        Class providing interface to pyAPT for APT protocol stepper/servo motors.
        Presently reads the position but does not move the motor.
        
        Specify 'serial_number' in the params dict at initialization to choose which motor to drive if you have multiple. 
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.serial_number = params['serial_number']
        self.name = params['name']
        self.driver = 'pyapt'
        self.subdriver = 'None'
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet
        if params is not {}: self.scan(quiet=self.quiet)
        
        return

    # Detect if device is present - confirm serial_number visible to pyAPT
    def scan(self,override_params=None,quiet=False):
        self.port = None
        if override_params is not None: self.params = override_params
        
        # Check device is present on the bus.
        if 'bcdDevice' in self.params.keys():
            usbCoreDev = usb.core.find(idVendor=self.params['vid'],idProduct=self.params['pid'],\
                             bcdDevice=self.params['bcdDevice'])
        else:
            usbCoreDev = usb.core.find(idVendor=self.params['vid'],idProduct=self.params['pid'])
            
        if usbCoreDev is None:
            raise pyLabDataLoggerIOError("USB Device %s not found" % self.params['name'])

        # Parse driver parameters
        self.bus = usbCoreDev.bus
        self.adds = usbCoreDev.address
        
        # Find the matching pyAPT device seen on the USB tree, ensure it exists
        try:
            cprint( '\tLooking for APT controllers', 'green')
            drv = pylibftdi.Driver()
            controllers = drv.list_devices()
        except:
            raise RuntimeError("Error loading FTDI drivers. You may need superuser priveliges.")
        
        if self.serial_number is None:
            for controller in controllers:
                cprint( controller, 'magenta' )
                con = pyAPT.Controller(serial_number=controller[2])
                print('\t',con.info())
                if fmatch(con,self.bus,self.adds): self.serial_number = controller[2]
            
        if self.serial_number is None:
            cprint( "Could not open port to device.", 'red', attrs=['bold'])
        else: self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open socket)
    def activate(self,quiet=False):
        self.config['channel_names']=['position_rel','position_abs','velocity_set']
        self.config['scale']=[1.]*len(self.config['channel_names'])
        self.config['offset']=[0.]*len(self.config['channel_names'])
        self.params['n_channels']=3
        self.config['Home']=False
        self.config['MoveRel']=0.
        self.params['raw_units']=['mm','mm','mm/s']
        self.config['eng_units']=['mm','mm','mm/s']
        
        # Open socket to the pyAPT device.
        self.dev = pyAPT.MTS50(serial_number=self.serial_number)
        self.driverConnected=True
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: 
            print( '\t'+str(self.params['name']) )
            self.pprint()
        return

    # Deactivate connection to device (close socket)
    def deactivate(self):
        del self.dev
        self.driverConnected=False
        return

    # Apply configuration changes
    def apply_config(self):
        assert self.dev
    
        # Change velocity parameters?    
        min_vel, acc, max_vel = self.dev.velocity_parameters()
        if (acc != self.config['acc']) or (max_vel != self.config['max_vel']):
            self.dev.set_velocity_parameters(self.config['acc'], self.config['max_vel'])
            
        # Move?
        if self.config['MoveRel'] is not None:
            if self.config['MoveRel'] != 0:
                self.dev.move(dist)
                self.config['MoveRel']=0.
                
        # Home?
        elif self.config['Home']:
            self.dev.home(velocity=self.config['HomingVelocity'])
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
    
    # Handle query for values
    def query(self, reset=False):

        # Check port open
        assert(self.dev)#: raise pyLabDataLoggerIOError("Could not communicate with pyAPT device")
        
        # If first time or reset, get configuration
        if (not 'raw_units' in self.params) or reset:           
            min_vel, acc, max_vel = self.dev.velocity_parameters()
            homingParams = self.dev.request_home_params()
            raw_min_vel, raw_acc, raw_max_vel = self.dev.velocity_parameters(raw=True)
            
            self.config['acc']=acc
            self.config['max_vel']=max_vel
            self.config['HomingVelocity']=homingParams[1]
            self.params['min_vel']=min_vel
            self.params['raw_min_vel']=raw_min_vel
            self.params['raw_acc']=raw_acc
            self.params['raw_max_vel']=raw_max_vel
        
            # Don't overwrite 'name', it'll return something generic like "KDC101 Servo Drive"
            self.params['pyapt_device_name']='%s %s' % (self.dev.info()[4].decode('latin-1'), self.dev.serial_number)
            
        # Get values
        self.lastValue = [self.dev.position(),self.dev.position(raw=True),self.dev.status().velocity]
        
        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


