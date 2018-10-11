"""
    Main device class for pyPiDataLogger
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 1.0.0
    @date 27/05/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

import datetime

class device:
    """ Main class defining a device in pyPiDataLogger.
        This class is inherited by more specific sub-categories of devices i.e. USB. """

    def __init__(self):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = {} # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "untitled device"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        pass

    # Detect if device is present
    def scan(self):
        print "scan method not yet implemented for",self.name

    # Establish connection to device (ie open serial port)
    def activate(self):
        print "activate method not yet implemented for",self.name

    # Deactivate connection to device (ie close serial port)
    def deactivate(self):
        print "deactivate method not yet implemented for",self.name

    # Apply configuration changes to the driver
    def apply_config(self):
        print "apply_config not yet implemented for",self.name

    # Update configuration (ie change sample rate or number of samples)
    def update_config(self,config_keys={}):
        for key in config_keys.keys():
            self.config[key]=self.config_keys[key]
        self.apply_config()
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        return self.lastValue

    def updateTimestamp(self):
        self.lastValueTimestamp = datetime.datetime.now()

    # Re-establish connection to device.
    def reset(self):
        self.deactivate()
        self.scan()
        if self.driverConnected: self.activate()
        else: print "Error resetting %s: device is not detected" % self.name

