"""
    Thorlabs Scientific camera device class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @version 1.0.1
    @date 17/09/2020
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

from device import device, pyLabDataLoggerIOError
import numpy as np
import datetime, time, subprocess, sys
from termcolor import cprint

try:
    import usb.core
    import matplotlib.pyplot as plt
    from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
    from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK
    from thorlabs_tsi_sdk.tl_mono_to_color_enums import COLOR_SPACE
    from thorlabs_tsi_sdk.tl_color_enums import FORMAT

except ImportError:
    cprint( "Please install Thorlabs Scientific Camera Linux SDK and PyUSB", 'red', attrs=['bold'])
    raise

########################################################################################################################
class thorcamDevice(device):
    """ Class providing support for Thorlabs scientific cameras.
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.driver = self.params['driver'].split('/')[1:]
        self.quiet = quiet
        
        if not 'live_preview' in self.params:
            if not 'live_preview' in kwargs:
                self.live_preview=False
            else: self.live_preview=kwargs['live_preview']
        else: self.live_preview=self.params['live_preview']
            
        if not 'ID' in self.params: self.params['ID'] = None # default OpenCV camera ID number
        if not 'debugMode' in self.params: self.params['debugMode']=False
        
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

    # Establish connection to device
    def activate(self,quiet=False):
        
        # begin camera id block
        self.userChoseStream = False
        validCamRange = [None, None]
        
        self.camera_sdk = TLCameraSDK()
        self.mono_to_color_sdk = MonoToColorProcessorSDK()
        
        try:
            self.available_cameras = self.camera_sdk.discover_available_cameras()
        except UnicodeDecodeError:
            cprint("Thorlabs SDK Error: Please power cycle camera",'red',attrs=['bold'])
            exit()
            
        if len(self.available_cameras) < 1:
            cprint("no cameras detected! Check udev rules",'red',attrs=['bold'])
            return
        elif len(self.available_cameras) > 1:
            for i in range(len(self.available_cameras)):
                print("%i: %s" % (i,self.available_cameras[i]))
            while not self.params['ID'] in validCamRange:
                try:
                    self.params['ID']=int(raw_input("\tPlease select camera ID [0-%i]:" % (len(self.available_cameras)-1)))
                    self.userChoseStream = True
                except:
                    pass
        else:
            self.params['ID']=0
        
        # End camera id block
        
        # Set up configuration for number of frames to capture per query event
        
        if 'n_frames' in self.params: self.config['n_frames'] = self.params['n_frames']
        else: self.config['n_frames'] = 1
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        self.driverConnected=False
        del self.opencvdev
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
            self.frame_counter = -1 # reset frame counter. It'll be incremented up to zero before the first save.
            
            # Try to open camera stream.
            self.camera =  self.camera_sdk.open_camera(self.available_cameras[self.params['ID']])
            self.camera.frames_per_trigger_zero_for_unlimited = 0  # start camera in continuous mode
            self.camera.image_poll_timeout_ms = 2000  # 2 second timeout
            self.driverConnected=True
            
            # Setup post-processor for colour images
            self.mono_to_color_processor = self.mono_to_color_sdk.create_mono_to_color_processor(
                self.camera.camera_sensor_type,
                self.camera.color_filter_array_phase,
                self.camera.get_color_correction_matrix(),
                self.camera.get_default_white_balance_matrix(),
                self.camera.bit_depth)
            self.mono_to_color_processor.color_space = COLOR_SPACE.SRGB  # sRGB color space
            self.mono_to_color_processor.output_format = FORMAT.RGB_PIXEL  # data is returned as sequential RGB values
            self.params['red gain']=red_gain=self.mono_to_color_processor.red_gain
            self.params['green gain']=green_gain=self.mono_to_color_processor.green_gain
            self.params['blue gain']=blue_gain=self.mono_to_color_processor.blue_gain
            
            if self.live_preview:
                self.fig = plt.figure()
                self.ax = self.fig.add_subplot(111)
                self.ax.axis('off')
                #plt.ion()
                plt.show(block=False)
                plt.pause(.1)


        # Check
        try:
            assert(self.camera)
            if self.camera is None: raise pyLabDataLoggerIOError
        except:
            cprint( "Connection to the device is not open.", 'red', attrs=['bold'])
        

        # Get Image(s)
        rawFrames = []
        self.camera.arm(self.config['n_frames'])
        self.params['width'] = self.camera.image_width_pixels
        self.params['height'] = self.camera.image_height_pixels
        for j in range(self.config['n_frames']):
            self.camera.issue_software_trigger()
            rawframe = self.camera.get_pending_frame_or_null()
            self.frame_counter += 1 # increment counter even if image not returned
            rawFrames.append(rawframe)
            if rawframe is None:
                cprint("\tNo frame arrived from Thorlabs camera within the timeout!",'red')
        self.camera.disarm()
            
        if not self.quiet:
            cprint("\tCaptured %i/%i frames" % (len([f for f in rawFrames if f is not None]),self.config['n_frames']),'green')
        
        # Post process image(s)
        self.lastValue=[]
        livePreviewImg=None
        for rawframe in rawFrames:
            if rawframe is None:
                self.lastValue.append(np.nan)
            else:
                # this will give us a resulting image with 3 channels (RGB) and 16 bits per channel, resulting in 48 bpp
                color_image_16bit = self.mono_to_color_processor.transform_to_48(rawframe.image_buffer, self.params['width'], self.params['height'])
                # this will give us a resulting image with 4 channels (RGBA) and 8 bits per channel, resulting in 32 bpp
                #color_image = self.mono_to_color_processor.transform_to_32((rawframe.image_buffer, self.params['width'], self.params['height'])
                # this will give us a resulting image with 3 channels (RGB) and 8 bits per channel, resulting in 24 bpp
                color_image_8bit = self.mono_to_color_processor.transform_to_24(rawframe.image_buffer, self.params['width'], self.params['height'])
                # copy to lastValue
                if livePreviewImg is None: livePreviewImg = color_image_8bit[...].reshape(self.params['height'], self.params['width'], 3)
                self.lastValue.append(color_image_16bit[...].reshape(self.params['height'], self.params['width'], 3))
                
        # Set up live preview mode if requested
        if self.live_preview:
            cprint("\tlive_preview: displaying frame_%08i %s" % (self.frame_counter,livePreviewImg.shape), 'green')
            try:
                assert self.imshow
                self.imshow.set_data(livePreviewImg)
            except:
                self.imshow = self.ax.imshow(livePreviewImg)

            try:
                self.ax.set_title("Frame %06i : %s" % (self.frame_counter,self.lastValueTimestamp))
                self.fig.canvas.draw()
                #plt.show(block=False)
                plt.pause(0.01) # 10 ms for window to refresh itself.
            except:
                cprint( "\tError updating Thorlabs preview window", 'red', attrs=['bold'])

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
                # Swap to uint16, this might not work in HDFView but keep all the bits anyway! 17/9/20
                dset=dg.create_dataset(dsname, data=np.flip(self.lastValue[j],axis=2), dtype='uint16', chunks=True,\
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

