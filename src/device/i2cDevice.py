"""
    I2C device class - for Linux
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 11/10/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from device import device
import datetime, time
import numpy as np


########################################################################################################################
class i2cDevice(device):
    """ Class providing support for I2C devices. This class should not be used directly, it provides
        common functions for specific i2c devices. """

    def __init__(self,params={}):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "untitled I2C device"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        
        # Default I2C bus parameters
        if not 'bus' in params.keys(): params['bus']=1
        
        if params is {}: return
        self.scan()
        return

    # Detect if a device is present on bus
    def scan(self,override_params=None):
        if override_params is not None: self.params = override_params
        
        if not 'address' in self.params.keys():
            print "Error, no I2C address specified"
            return
        
        try:
            import smbus
            device_addresses=[]
            bus = smbus.SMBus(self.params['bus'])
            for a in range(128):
                try:
                    bus.write_byte(a)
                    device_addresses.append(hex(a))
                except IOError: # exception if read_byte fails
                    pass
            if len(device_addresses) ==0 :
                print "Error, no I2C devices found on bus %i" % self.params['bus']
                return
            elif not self.params['address'] in device_addresses:
                print "Error, address",self.params['address'],"not found (found",device_addresses,")"
                return
            self.activate()
            
        except ImportError:
            print "Error, smbus module could not be loaded"
            return


