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

try:
    import pylibftdi
    import pyAPT
except ImportError:
    print "Please install pyAPT and pylibftdi"
    exit()


########################################################################################################################
class pyAPTDevice(device):
    """
        Class providing interface to pyAPT. Presently reads the position but does not move the motor.
    """

    def __init__(self,params={},quiet=False):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.serial_number = params['serial_number']
        self.name = "pyAPT device" # %s" % self.serial_number
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present - confirm serial_number visible to pyAPT
    def scan(self,override_params=None,quiet=False):
        self.port = None
        if override_params is not None: self.params = override_params
        
        # Find the matching pyAPT device seen on the USB tree, ensure it exists
        print '\tLooking for APT controllers'
        drv = pylibftdi.Driver()
        controllers = drv.list_devices()
        if self.serial_number is None:
            for controller in controllers:
                print controller
                con = pyAPT.Controller(serial_number=controller[2])
                print '\t',con.info()
                if fmatch(con): self.serial_number = controller[2]
            
        if self.serial_number is None:
            print "Could not open port to device."
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
        
        # Open socket to the pyAPT device.
        self.dev = pyAPT.MTS50(serial_number=self.serial_number)
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close socket)
    def deactivate(self):
        del self.dev
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
        else: print "Error resetting %s: device is not detected" % self.name
    
    # Handle query for values
    def query(self, reset=False):

        # Check port open
        assert(self.dev)#: raise IOError("Could not communicate with pyAPT device")
        
        # If first time or reset, get configuration
        if (not 'raw_units' in self.params) or reset:           
            min_vel, acc, max_vel = self.dev.velocity_parameters()
            homingParams = con.request_home_params()
            raw_min_vel, raw_acc, raw_max_vel = self.dev.velocity_parameters(raw=True)

            self.config['acc']=acc
            self.config['max_vel']=max_vel
            self.config['HomingVelocity']=homingParams['velocity']
            self.params['min_vel']=min_vel
            self.params['raw_min_vel']=raw_min_vel
            self.params['raw_acc']=raw_acc
            self.params['raw_max_vel']=raw_max_vel
            
            print self.dev.info()
            print self.dev.status()
            unit=self.dev.fget_units_of_motor()
            self.params['raw_units']=[unit]
            self.config['eng_units']=[unit]
            self.params['name']='%s %s' % (self.dev.fget_device_descriptor(),self.dev.fget_device_serial_number())
            
        # Get values
        self.lastValue = [self.dev.position(),self.dev.position(raw=True),self.dev.status().velocity]
        
        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue

