"""
    libcamera device class
    Currently just uses the picamera library for Rasberry Pi.
    In future can be a generic CSI/CSI2 interface for other SBCs.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.0
    @date 20/12/2020
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
import datetime, time, subprocess, sys
from termcolor import cprint

try:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
    import matplotlib.pyplot as plt
except ImportError:
    cprint( "Please install libcamera (libcamera.org)", 'red', attrs=['bold'])
    raise

########################################################################################################################
class libcameraDevice(device):
    """ Class providing support for generic libcamera devices.
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized camera"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        #self.driver = self.params['driver'].split('/')[1:]
        
        if 'resolution' in kwargs:
            self.params['resolution']=kwargs['resolution']

        if not 'live_preview' in self.params:
            if not 'live_preview' in kwargs:
                self.live_preview=False
            else: self.live_preview=kwargs['live_preview']
        else: self.live_preview=self.params['live_preview']
        
        if not 'debugMode' in self.params: self.params['debugMode']=False
        
        self.quiet = quiet

        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        # check CSI interface is available.
        # expect to see "supported=1 detected=1" or similar
        try:
            '''
            detect=''
            if 'run' in dir(subprocess):
                detect=subprocess.run(["vcgencmd","get_camera"])
            else:
                detect=subprocess.call(["vcgencmd","get_camera"])
            '''
            p = subprocess.Popen(['vcgencmd', 'get_camera'],\
                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            detect, err = p.communicate()
            if int(detect.strip().split('etected=')[-1][0]) >= 1:
                self.activate(quiet=quiet)
            else:
                raise IOError
        except:
            cprint("No camera available",'red',attrs={'bold'})
            pass
        
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
        
        # Try to open camera stream.
        self.camera = PiCamera()
        self.rawCapture = PiRGBArray(self.camera)
        time.sleep(0.1) # warmup time
        self.driverConnected=True
        
        if 'n_frames' in self.params: self.config['n_frames'] = self.params['n_frames']
        else: self.config['n_frames'] = 1
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        self.driverConnected=False
        del self.camera
        del self.rawCapture
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        #subdriver = self.params['driver'].split('/')[1:]
        try:
            assert(self.deviceClass)
            if self.deviceClass is None: raise pyLabDataLoggerIOError("Could not access device.")
            '''
            # Apply subdriver-specific variable writes
            if subdriver=='?':
                #...
                pass
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
            '''
        except ValueError:
            cprint( "%s - Invalid setting requested" % self.name, 'red', attrs=['bold'])
        
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
        else: cprint( "Error resetting %s: device is not detected" % self.name, 'red', attrs=['bold'])
   

    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.rawCapture)
            assert(self.camera)
            if self.camera is None: raise pyLabDataLoggerIOError
        except:
            cprint( "Connection to the device is not open.", 'red', attrs=['bold'])

        # If first time or reset, get configuration (ie units)
        if not 'raw_units' in self.params.keys() or reset:

            # Set up device
            self.name = 'CSI camera'
            if self.config['n_frames'] == 1: self.config['channel_names']=['Image']
            else: self.config['channel_names']=['Frame %i' % j  for j in range(self.config['n_frames'])]
            self.params['raw_units']=['Intensity']
            self.config['eng_units']=['Intensity']
            self.config['scale']=[1.]
            self.config['offset']=[0.]
            self.params['n_channels']=self.config['n_frames']
            self.frame_counter = -1 # reset frame counter. It'll be incremented up to zero before the first save.
            if 'resolution' in self.params:
                self.camera.resolution = self.params['resolution']
                if not self.quiet: cprint("\tSet resolution to %s." % str(self.params['resolution']), 'cyan')

            if self.live_preview:
                self.fig = plt.figure()
                self.ax = self.fig.add_subplot(111)
                self.ax.axis('off')
                #plt.ion()
                plt.show(block=False)
                plt.pause(.1)

        # Get Image(s)
        self.lastValue = []
        for j in range(self.config['n_frames']):
            self.rawCapture.truncate(0) # reset buffer
            self.camera.capture(self.rawCapture, format="bgr")
            frame=self.rawCapture.array
            self.frame_counter += 1 # increment counter even if image not returned
            
            self.lastValue.append(frame[...])
            # Set up live preview mode if requested
            if j==0 and self.live_preview:
                transform = lambda I: np.flip(I,axis=-1)
                cprint("\tlive_preview: displaying frame_%08i" % self.frame_counter, 'green')
                try:
                    assert self.imshow
                    self.imshow.set_data(transform(self.lastValue[-1]))
                except:
                    self.imshow = self.ax.imshow(transform(self.lastValue[-1]))

                try:
                    self.ax.set_title("Frame %06i : %s" % (self.frame_counter,self.lastValueTimestamp))
                    self.fig.canvas.draw()
                    #plt.show(block=False)
                    plt.pause(0.01) # 10 ms for window to refresh itself.
                except:
                    cprint( "\tError updating libcamera device window", 'red', attrs=['bold'])

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
            cprint( "Please install h5py", 'red', attrs=['bold'])
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
                    cprint( "\tOverwriting image %s in HDF5 log file!" % dsname, 'yellow')
                    del dg[dsname]
                
                # Flip colours in dataset - 21/5/20
                dset=dg.create_dataset(dsname, data=np.flip(self.lastValue[j],axis=2), dtype='uint8', chunks=True,\
                                        compression='gzip', compression_opts=1) # apply fast compression
                
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

