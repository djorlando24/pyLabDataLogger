"""
    I2C device class - for Linux
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 06/02/2019
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from device import device, pyLabDataLoggerIOError
import datetime, time
import numpy as np

""" Scan for available and unused i2c bus addresses that may contain
    devices we can talk to. """
def scan_for_devices(bus=1):
    import smbus
    bus = smbus.SMBus(bus) # 1 indicates /dev/i2c-1
    devices=[]
    for device in range(128):
       try:
          bus.read_byte(device)
          devices.append(hex(device))
       except:
          continue
    return devices

""" Load devices based on a-priori knowledge of what addresses on the bus
    correspond to what supported hardware. This won't work for devices that
    share addresses. """
def load_i2c_devices(devices=None,bus=1,**kwargs):
    if devices is None: devices=scan_for_devices(bus)
    device_list=[]
    for address in devices:
        if address=='0x48' or address=='0x49':
            from pyLabDataLogger.device import ads1x15Device
            device_list.append(ads1x15Device.ads1x15Device(params={'address':address, 'bus':bus},**kwargs))
        elif address=='0x77':
            from pyLabDataLogger.device import bmp085Device
            device_list.append(bmp085Device.bmp085Device(params={'address':address, 'bus':bus},**kwargs))
        else:
            print "I don't know what to do with I2C device at address",address
    return device_list



########################################################################################################################
class i2cDevice(device):
    """ Class providing support for I2C devices. This class should not be used directly, it provides
        common functions for specific i2c devices. """

    def __init__(self,params={},quiet=False,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "untitled I2C device"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        
        # Default I2C bus parameters
        if not 'bus' in params.keys(): params['bus']=1
        
        # apply kwargs to params
        for k in ['differential','gain']:
           if k in kwargs: self.params[k]=kwargs[k]
        # apply kwargs to config
        for k in ['channel_names']:
           if k in kwargs: self.config[k]=kwargs[k]
        
        if params is {}: return
        self.scan(quiet=quiet)
        return

    # Detect if a device is present on bus
    def scan(self,override_params=None,quiet=False):
        if override_params is not None: self.params = override_params
        
        if not 'address' in self.params.keys():
            print "Error, no I2C address specified"
            return
        
        try:
            import smbus
            bus = smbus.SMBus(self.params['bus'])
            try:
                bus.read_byte(int(self.params['address'],16))
            except:
                print "Error, no I2C devices found on bus %i address %s" % (self.params['bus'],self.params['address'])
                raise
                return

            self.activate()
            self.query()
            if not quiet: self.pprint()
            
        except ImportError:
            print "Error, smbus module could not be loaded"
            return
