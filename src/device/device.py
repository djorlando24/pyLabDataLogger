"""
    Main device class for pyPiDataLogger
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 12/10/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

import datetime
import numpy as np
import sys

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

    # Update configuration (ie change sample rate or number of samplezzs)
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

    # Print values with units
    def pprint(self,lead='\t'):
        show_scaled = ('eng_units' in self.config) and ('scale' in self.config) and\
                      ('offset' in self.config) and ('eng_units' in self.config) and\
                      not (np.all(np.array(self.config['scale'])==1.) and  np.all(np.array(self.config['offset'])==0.))
        # Scalars.
        if isinstance( self.lastValue[0], float ) or isinstance( self.lastValue[0], int ):
            if 'raw_units' in self.params:
                sys.stdout.write(lead+'Raw values: ')
                for n in range(self.params['n_channels']):
                    sys.stdout.write(u'%g %s, ' % (self.lastValue[n],self.params['raw_units'][n]))
                sys.stdout.write('\n')
            else:
                print lead+'Raw values:',self.lastValue
            # Only show the scaled units if they exist.
            if show_scaled:
                for n in range(self.params['n_channels']):
                    sys.stdout.write(u'%f %s, ' % (self.lastScaled[n],self.params['eng_units'][n])) 
                sys.stdout.write('\n')
    
        # Vectors
        elif isinstance( self.lastValue[0], list) or isinstance(self.lastValue[0], np.ndarray):
            for n in range(self.params['n_channels']):
                if ~show_scaled: print lead+u'%i: %s = %s %s' % (n,self.config['channel_names'][n],\
                                    self.lastValue[n],self.params['raw_units'][n])
                else: print lead+u'%i: %s = %s %s \t %s %s' % (n,self.config['channel_names'][n],self.lastValue[n],\
                        self.params['raw_units'][n],self.lastScaled[n],self.config['eng_units'][n])
                    
        return
