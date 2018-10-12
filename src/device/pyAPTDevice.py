"""
    pyAPT device class - Thorlabs stepper motors
    
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

from device import device
import numpy as np
import datetime, time

########################################################################################################################
class pyAPTDevice(device):
    """
        Class providing interface to pyAPT. Presently reads the position but does not move the motor.
    """

    def __init__(self,params={},quiet=False):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "pyAPT device %i" % int(params['serial_number'])
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.Serial = params['serial_number']
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        self.port = None
        if override_params is not None: self.params = override_params
        
        # Find the matching pyAPT device seen on the USB tree, ensure it exists
        success = ffind_pyapt_device(self.params['serial_number'])
        
        if not success: 
            print "Could not open port to device."
        else: self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open socket)
    def activate(self,quiet=False):
        self.config['channel_names']=['position']
        self.config['scale']=[1.]
        self.config['offset']=[0.,]
        self.params['n_channels']=1
        
        # Open socket to the pyAPT device.
        self.dev = fopen_pyapt_connection(self.params['serial_number'])
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close socket)
    def deactivate(self):
        self.dev.close_pyapt_connection()
        return

    # Apply configuration changes
    def apply_config(self):
        # currently no parameters can be remotely configured
        # In future we could switch jog/step mode and the step size
        # or write a requested position/homing.
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
        else: print "Error resetting %s: device is not detected" % self.name
    
    # Handle query for values
    def query(self, reset=False):

        # Check port open
        if not self.dev.fcheck_motor_connection(): raise IOError("Could not communicate with pyAPT device")
        
        # If first time or reset, get configuration
        if (not 'raw_units' in self.params) or reset:
            unit=self.dev.fget_units_of_motor()
            self.params['raw_units']=[unit]
            self.config['eng_units']=[unit]
            self.params['name']='%s %s' % (self.dev.fget_device_descriptor(),self.dev.fget_device_serial_number())
            
        # Get values
        self.lastValue = self.dev.fget_position_of_motor()
        
        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


