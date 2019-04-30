"""
    OpenCV webcam device class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 30/04/2019
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
import datetime, time

try:
    import cv2
    import usb.core
except ImportError:
    print "Please install OpenCV and PyUSB"
    raise

########################################################################################################################
class opencvDevice(device):
    """ Class providing support for generic OpenCV-compatible webcams.
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.driver = self.params['driver'].split('/')[1:]
        
        if not 'ID' in self.params: self.params['ID'] = 0 # default OpenCV camera ID number
        
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        # check USB device exists
        try:
            self.usbdev = usb.core.find(idVendor=self.params['vid'], idProduct=self.params['pid'])
            self.activate(quiet=quiet)
        except:
            raise
        
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
        
        self.opencvdev = cv2.VideoCapture(self.params['ID'])
        self.driverConnected=True
        if 'n_frames' in self.params: self.config['n_frames'] = self.params['n_frames']
        else: self.config['n_frames'] = 1
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        # ...
        self.driverConnected=False
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        subdriver = self.params['driver'].split('/')[1:]
        try:
            assert(self.deviceClass)
            if self.deviceClass is None: raise pyLabDataLoggerIOError("Could not access device.")
            
            # Apply subdriver-specific variable writes
            if subdriver=='?':
                #...
                pass
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
        
        except ValueError:
            print "%s - Invalid setting requested" % self.name
            print "\t(V=",self.params['set_voltage'],"I=", self.params['set_current'],")"
        
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
        else: print "Error resetting %s: device is not detected" % self.name
   

    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.opencvdev)
            if self.opencvdev is None: raise pyLabDataLoggerIOError
        except:
            print "Connection to the device is not open."

        # If first time or reset, get configuration (ie units)
        if not 'raw_units' in self.params.keys() or reset:

            # Set up device
            self.name = self.params['name'] # from usbDevice lookup table, usb descriptor data often empty
            if self.config['n_frames'] == 1: self.config['channel_names']=['Image']
            else: self.config['channel_names']=['Frame %i' % j  for j in range(self.config['n_frames'])]
            self.params['raw_units']=['Intensity']
            self.config['eng_units']=['Intensity']
            self.config['scale']=[1.]
            self.config['offset']=[0.]
            self.params['n_channels']=self.config['n_frames']
            self.frame_counter = 0 # reset frame counter

        # Get Image(s)
        self.lastValue = []
        for j in range(self.config['n_frames']):
            ret, frame = self.opencvdev.read()
            self.frame_counter += 1 # increment counter even if image not returned
            if ret:
                self.lastValue.append(frame[...])
            else:
                self.lastValue.append(np.array((np.nan,)))
                raise pyLabDataLoggerIOError("OpenCV Webcam capture failed")

        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


    # log to HDF5 file - overload function
    def log_hdf5(self, filename, max_records=None):
        try:
            import h5py
        except ImportError:
            print "Please install h5py"
            return
        
        # Open file
        with h5py.File(filename, 'a') as fh:

            # Load group for this device.
            if 'name' in self.config: devname = self.config['name']
            elif 'name' in self.params: devname = self.params['name']
            else: devname = self.name
            if devname in fh: dg = fh[devname]
            else:
                dg = fh.create_group(devname)
                # On creation, add attributes from config and params
                for attr in self.params.keys():
                    dg.attrs[attr] = repr(self.params[attr])
                for attr in self.config.keys():
                    dg.attrs[attr] = repr(self.config[attr])

            # Create/update timestamp dataset
            # Each device has a lastValueTimestamp which can vary a bit between devices due to latency issues.
            if 'timestamp' in dg:
                td = dg['timestamp']
                td.resize([td.shape[0]+1,])
                td[-1] = str(self.lastValueTimestamp)
            else:
                dg.create_dataset('timestamp',data=[str(self.lastValueTimestamp)],maxshape=(max_records,))


            # Write images into dg...
            for j in range(len(self.lastValue)):
                dsname = 'frame_%08i' % (self.frame_counter-len(self.lastValue)+j+1)
                if dsname in dg:
                    print "\tOverwriting image %s in HDF5 log file!" % dsname
                    del dg[dsname]
                dset=dg.create_dataset(dsname, data=self.lastValue[j], dtype='uint8', chunks=True)
                #Set the image attributes
                dset.attrs.create('CLASS', 'IMAGE')
                dset.attrs.create('IMAGE_VERSION', '1.2')
                dset.attrs.create('IMAGE_SUBCLASS', 'IMAGE_TRUECOLOR')
                dset.attrs.create('INTERLACE_MODE', 'INTERLACE_PIXEL')
                #dset.attrs['IMAGE_COLORMODEL'] = 'RGB'
            
            fh.close()

    # log to text file - overload function
    def log_text(self, filename):
        # In "text" mode, perhaps just save a JPEG file?
        raise RuntimeError("Not implemented")

