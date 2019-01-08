"""
    Measurement Computing USB device class
    based on the mcc-libusb driver by Warren J. Jasper
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 29/11/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from device import device, pyLabDataLoggerIOError
import numpy as np
import site, itertools, glob
import datetime, time

import ctypes, ctypes.util, struct
from ctypes import c_int, c_bool, py_object, c_long, c_uint, c_ulong, c_float, c_uint8, c_uint16, POINTER, cast, addressof, c_double, c_char_p
#from threading import Lock

# This is the ScanList struct defined by the interface C header file
class ScanList_t(ctypes.Structure):
     _fields_ = [("mode", c_uint8),("range", c_uint8),("channel", c_uint8)]

# This is the pyudev_t struct defined by the interface C header file
# it has a pyCapsule object that points to the usb device handle
# and some boolean flags etc. required for mode of operation etc.
class pyudev_t(ctypes.Structure):
     _fields_ = [("udev_capsule", py_object),
                 ("usb1608GX_2AO", c_bool),
                 ("model", c_int),
                 ("n_channels", c_int),
                 ("n_samples", c_int),
                 ("table_AIN", c_float*16),
                 ("table_AO", c_float*16),
                 ("list", POINTER(ScanList_t)),
                ]


########################################################################################################################
class mcclibusbDevice(device):
    """ Class providing support for Measurement Computing USB devices
        based on the mcc-libusb driver by Warren J. Jasper
    """

    def __init__(self,params={},quiet=False,**kwargs):

        # Add more here when more devices are supported!
        self.supported_devices = ['mccusb1608G']

        # Try to find the libmccusb DLL at runtime
        try:
            for lib in ['hidapi-libusb','mccusb']:
                libname = ctypes.util.find_library(lib)
                if libname is None: raise OSError
                _lib=ctypes.CDLL(libname, mode=ctypes.RTLD_GLOBAL)
        except OSError:
            print "Please install mcc-libusb"
            return
        self.libmccusb = _lib
        if not quiet: print "\tLoaded %s" % _lib._name

        # Get subdriver
        self.subdriver = ''.join(params['driver'].split('/')[1:])
        # Check it is supported
        if not self.subdriver in self.supported_devices:
            print "\tError. Device %s not supported." % self.subdriver
            print "\tValid choices are:",self.supported_devices
            return
        
        # Find DLLs for specific devices generated at build time from src/mcclibusb
        sites = site.getsitepackages(); sites.append(site.USER_SITE)
        libname = self.subdriver[:]
        for libext in ['so','dylib','dll','a']:
            path_to_lib = list(itertools.chain.from_iterable([ glob.glob(p+'/lib'+libname+'.'+libext)\
                                        for p in sites ]))
            if len(path_to_lib)>0: break
        if len(path_to_lib)==0: print("\tWarning - can't find lib%s" % libname)
        else: self.libpath = path_to_lib[0]

        # Set up the device class
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.quiet = quiet
        
        if params is not {}: self.scan()
        
        return




    # Detect if device is present
    def scan(self,override_params=None):
        
        if override_params is not None: self.params = override_params

        if not self.quiet: print '\tScanning for devices'

        # Load device-specific library found in __init__.
        self.L = ctypes.cdll.LoadLibrary(self.libpath)        
        if not self.quiet: print '\tLoaded',self.L._name

        # Scan for device
        self.L.detect_device.restype = pyudev_t
        self.pyudev = self.L.detect_device(c_bool(self.quiet))
        if self.pyudev.udev_capsule is None: return
        
        self.activate()
        return




    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
        
        # Activate device
        self.L.activate_device.argtypes=[pyudev_t, c_bool]
        self.L.activate_device.restype=pyudev_t
        self.pyudev = self.L.activate_device(self.pyudev, c_bool(self.quiet))
        if self.pyudev == 0:
            raise pyLabDataLoggerIOError("Communication with the device failed.")

        if self.pyudev.model == 1: self.name = 'MCC USB-1608G'
        elif self.pyudev.model == 2: self.name = 'MCC USB-1608GX'
        elif self.pyudev.model == 3: self.name = 'MCC USB-1608GX_2AO'
        elif self.pyudev.model == 4: self.name = 'MCC USB-1608G'
        elif self.pyudev.model == 5: self.name = 'MCC USB-1608GX'
        elif self.pyudev.model == 6: self.name = 'MCC USB-1608GX_2AO'
        else: raise ValueError("\tUnknown model number")
        self.driverConnected=True
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not self.quiet: self.pprint()
        return

    
    # Deactivate connection to device (close serial port)
    def deactivate(self):
        self.L.deactivate_device.argtypes=[pyudev_t, c_bool]
        if self.L.deactivate_device(self.pyudev, c_bool(self.quiet)) ==0:
            raise pyLabDataLoggerIOError("Communication with the device failed.")
        self.driverConnected=False
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        
        try:
            assert(self.pyudev)

            # Differential or single ended mode:
            if not 'differential' in self.config:            
                if 'differential' in self.params:
                    self.config['differential']=self.params['differential']
                else:
                    self.config['differential']=True # default on            

            # Set up analog channels
            if self.config['differential']:
                self.config['channel_names']=['Analog input %i' % i for i in range(8)]
            else:
                self.config['channel_names']=['Analog input %i' % i for i in range(16)]
            self.params['n_channels']=len(self.config['channel_names'])
            self.params['raw_units']=['V']*self.params['n_channels']
            self.config['eng_units']=['V']*self.params['n_channels']            
            self.config['scale']=[1.]*self.params['n_channels']
            self.config['offset']=[0.]*self.params['n_channels']

            # Sampling rate and number of samples
            if not 'sample_rate' in self.config:
                if 'sample_rate' in self.params:
                    self.config['sample_rate']=self.params['sample_rate']
                else:
                    self.config['sample_rate']=1000. # Hz

            if not 'n_samples' in self.config:
                if 'n_samples' in self.params:
                    self.config['n_samples']=self.params['n_samples']
                else:
                    self.config['n_samples']=5

            # Gain range for analog inputs
            if not 'analog_input_gain' in self.config:            
                if 'analog_input_gain' in self.params:
                    if len(self.params['analog_input_gain']) < self.params['n_channels']:
                        raise IndexError("Insufficient number of analog_input_gain values given")
                    self.config['analog_input_gain']=self.params['analog_input_gain']
                else:
                    self.config['analog_input_gain']=[10]*self.params['n_channels'] # 10,5,2,1 V. Reset to 10V by default.
            for g in self.config['analog_input_gain']:
                if not g in [10,5,2,1]:
                    raise ValueError("Error setting analog gain for MCC USB device: valid options are 1,2,5,10 V")
            
            # Set up differential or single ended mode and apply analog gain ranges (sample rate set at run-time).
            gains = np.array(self.config['analog_input_gain'],dtype=np.uint8).ctypes.data_as(POINTER(c_uint8))
            self.L.set_analog_config.argtypes=[pyudev_t, c_bool, POINTER(c_uint8), c_int, c_bool]
            self.L.set_analog_config.restype=pyudev_t
            self.pyudev = self.L.set_analog_config(self.pyudev, c_bool(self.config['differential']), gains,\
                         c_int(self.config['n_samples']), c_bool(self.quiet))
            if self.pyudev==0: raise pyLabDataLoggerIOError("Unable to communicate with MCC USB device.")

            # Set up the 8 digital channels as a single input byte
            self.params['n_channels'] += 1
            self.config['channel_names'].append('Digital input')
            self.params['raw_units'].append('')
            self.config['eng_units'].append('')
            self.config['scale'].append(1.)
            self.config['offset'].append(0.)
            
            # Set up the two 20 MHz 32-bit counters as two additional channels
            self.params['n_channels'] += 2
            self.config['channel_names'].extend(['Counter 0','Counter 1'])
            self.params['raw_units'].extend(['Hz','Hz'])
            self.config['eng_units'].extend(['Hz','Hz'])
            self.config['scale'].extend([1.,1.])
            self.config['offset'].extend([0.,0.])

            # Configure digital I/O pins as inputs
            self.L.set_digital_direction.argtypes=[pyudev_t, c_bool, c_bool]
            ret = self.L.set_digital_direction(self.pyudev, c_bool(True), c_bool(self.quiet))
            if ret==0: raise pyLabDataLoggerIOError("Unable to communicate with MCC USB device.")
            
            # Set up triggering mode?
            # (not sure if supported by mcc-libusb)

            # Set up analog outputs, PWM/timer/function generator output
            # (all supported by mcc-libusb)
            # ...
        
        except ValueError:
            print "%s - Invalid setting requested" % self.name
            print "\t(V=",self.params['set_voltage'],"I=", self.params['set_current'],")"
        
        return

    # Update configuration (ie change sample rate or number of samples)
    def update_config(self,config_keys={}):
        # Check valid analog input gain
        for g in self.config['analog_input_gain']:
            if not g in [10,5,2,1]:
                raise ValueError("Error setting analog gain for MCC USB device: valid options are 1,2,5,10 V")
        # Apply to self.config
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

    # Read values from device.
    def get_values(self):
        Nvals = self.pyudev.n_channels * self.pyudev.n_samples
        analog_vals = np.empty((Nvals,))
        self.L.analog_read.argtypes=[pyudev_t, c_double, c_bool, POINTER(c_double)]
        if self.L.analog_read(self.pyudev, c_double(self.config['sample_rate']), c_bool(self.quiet),\
            analog_vals.ctypes.data_as(POINTER(c_double))) == 0:
            raise pyLabDataLoggerIOError("Communication with the device failed.") 
        analog_vals = analog_vals.reshape(self.pyudev.n_channels,self.pyudev.n_samples)

        # Currently, only one sampling of the digital IO and counter.
        # Would need to fold these into the analog read loop if we wanted real-time.
        self.L.digital_read.argtypes=[pyudev_t]
        self.L.digital_read.restype=c_uint8 # one unsigned int, containing all the bits in binary form.
        digital_vals = self.L.digital_read(self.pyudev)
        if digital_vals == None: raise pyLabDataLoggerIOError("Communication with the device failed.")

        self.L.counter_read.argtypes=[pyudev_t, c_int]
        self.L.counter_read.restype=c_uint16
        counter0 = self.L.counter_read(self.pyudev,0)
        counter1 = self.L.counter_read(self.pyudev,1) 
        if (counter0 == None) or (counter1 == None): raise pyLabDataLoggerIOError("Communication with the device failed.")
        
        self.lastValue = []
        for i in range(analog_vals.shape[0]):
            self.lastValue.append(analog_vals[i,:])
        self.lastValue.extend([digital_vals, counter0, counter1])
        
        return

    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.pyudev)
        except:
            print "Connection to the device is not open."

        # If first time or reset, get configuration (ie units)
        if not 'raw_units' in self.params.keys() or reset:
            self.apply_config()

        # Read values        
        self.get_values()

        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled=[]
        for i in range(len(lastValueSanitized)):
            self.lastScaled.append(np.array(lastValueSanitized[i]) * self.config['scale'][i] + self.config['offset'][i])
        self.updateTimestamp()
        return self.lastValue


