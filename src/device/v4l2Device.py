"""
    Video 4 Linux capture device support (v4l2)
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 18/03/2019
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
import h5py

try:
    import v4l2capture, select
except ImportError:
    print "Please install v4l2capture"
    raise

########################################################################################################################
class v4l2Device(device):
    """ Class providing support for Video4Linux2 (v4l2) video capture streams
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized v4l2 stream"
        self.vd = None
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.driver = self.params['driver'].split('/')
        self.subdriver = self.driver[1:]
        self.frame_counter = 0
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        # accept params['dev']='/dev/video0' for example
        if not 'dev' in self.params: 
            # Find /dev/video0 or similar relating to a USB device
            # v4l2-ctl --all | grep 'Bus info'  <   returns "	Bus info      : usb-0000:00:14.0-14" for example
            # we have params['vid'], params['pid'] and can use usb.core to get the bus and address to see if a match in above.
            self.params['dev'] = '/dev/video0'
        try:
            self.dev = self.params['dev']
            print "\tV4L2 device: %s" % self.dev
        except KeyError:
            print "No v4l2 device found."
            return
        if self.dev is not None: self.activate(quiet=quiet)
        return

    # Establish connection to device
    def activate(self,quiet=False):
        
        if 'width' in self.params: self.config['width'] = self.params['width']
        else: self.config['width'] = 720
        if 'width' in self.params: self.config['height'] = self.params['height']
        else: self.config['height'] = 480
        if 'fourcc' in self.params: self.config['fourcc'] = self.params['fourcc']
        else: self.config['fourcc'] = 'NTSC'
        if 'fourcc' in self.params: self.config['n_frames'] = self.params['n_frames']
        else: self.config['n_frames'] = 1
        
        # choose input for multi input devices?
        if not quiet:
            print "\tRequest %i x %i, fourcc = %s, capture %i frames" % (self.config['width'],self.config['height'],\
                        self.config['fourcc'],self.config['n_frames'])
        
        if 'uninitialized' in self.name:    
            self.name = '%s v4l2 stream' % self.dev
        
        try:
            self.vd = v4l2capture.Video_device(self.dev)
            size_x, size_y = self.vd.set_format(self.config['width'], self.config['height'])
            if not quiet: print "\tv4l2 device chose {0}x{1} res".format(size_x, size_y)
            self.config['width']=size_x
            self.config['height']=size_y
            self.vd.create_buffers(self.config['n_frames'])
            self.vd.queue_all_buffers()
            self.driverConnected=True
        except:
            raise
            # Need better error handling and useful error messages
            return
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        self.vd.close()
        self.vd = None
        self.driverConnected=False
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        try:
            assert(self.dev)
            if self.vd is None: raise pyLabDataLoggerIOError("Could not access device.")
        
            # Check self.config for video stream resolution, type, etc...
            self.query(reset=True)
            
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
            assert(self.vd)
            if self.vd is None: raise pyLabDataLoggerIOError
        except:
            print "Connection to the v4l2 stream is not open."

        # First-time configuration
        if not 'raw_units' in self.params.keys() or reset:
            self.name = "V4l2 capture device" # Get name !!
            self.config['channel_names']=['Image']
            self.params['raw_units']=['Intensity']
            self.config['eng_units']=['Intensity']
            self.config['scale']=[1.]
            self.config['offset']=[0.]
            self.params['n_channels']=len(self.config['channel_names'])

        # Capture frames
        self.vd.start()
        select.select((self.vd,),(),())
        try:
            self.image_data = self.vd.read_and_queue()
        except:
            pass
        self.lastValue = [np.frombuffer(self.image_data, dtype=np.uint8).reshape(self.config['height'],self.config['width'],3)] # 8 bit colour
        self.vd.stop()
        
        if reset: self.frame_counter=0
        else: self.frame_counter += self.config['n_frames']
        
        
        #self.lastValue = # image frame
        #self.lastScaled = # scaled image frame
        self.updateTimestamp()
        return self.lastValue
    
    
    # log to HDF5 file
    def log_hdf5(self, filename, max_records=None):
        assert(h5py)
        
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
            dset=dg.create_dataset('frame_%08i' % self.frame_counter, data=self.lastValue[0], dtype='uint8', chunks=True)
            #Set the image attributes
            dset.attrs.create('CLASS', 'IMAGE')
            dset.attrs.create('IMAGE_VERSION', '1.2')
            dset.attrs.create('IMAGE_SUBCLASS', 'IMAGE_TRUECOLOR')
            dset.attrs.create('INTERLACE_MODE', 'INTERLACE_PIXEL')
            #dset.attrs['IMAGE_COLORMODEL'] = 'RGB'
            
            fh.close()

    # log to text file
    def log_text(self, filename):
        # In "text" mode, perhaps just save a JPEG file?
        raise RuntimeError("Not implemented")