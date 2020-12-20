"""
    OpenCV webcam device class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @@version 1.1.0
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
    import cv2
    import usb.core
except ImportError:
    cprint( "Please install OpenCV and PyUSB", 'red', attrs=['bold'])
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
        self.MAX_CAMERAS = 16
        
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

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
        
        # begin camera id block
        self.userChoseStream = False
        validCamRange = [None, None]
        
        def user_choose_stream(validCamRange):
            if not quiet:
                print("\n\tMultiple webcams detected. OpenCV cannot automatically identify them.")
                print("\t(Your built-in webcam may be one of them).")
            self.params['ID']=-1
            while not self.params['ID'] in validCamRange:
                try:
                    self.params['ID']=int(input("\tPlease select OpenCV device %s: " % str(validCamRange)))
                    self.userChoseStream = True
                except:
                    pass
        
        if self.params['ID'] is None:
            # OpenCV 2 can have multiple video capture streams (i.e. from built-in webcams) and
            # it is not easy to determine which is the right one (this is apparently fixed in
            # OpenCV 3.

            # We will use a hack to figure this out. First check opencv is not already running capture
            try:
                assert(opencvdev)
                del opencvdev
            except:
                pass
            
            # Now try and open cameras in increasing number until we hit error condition!
            validCamRange = []
            for cam_num in range(self.MAX_CAMERAS):
                proc = subprocess.Popen([sys.executable,"-c",\
                                        "import cv2; print(cv2.__version__); dev=cv2.VideoCapture(%i)" % cam_num],\
                                        stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                stdout, stderr = proc.communicate()
                stdout = stdout.decode('ascii')
                stderr = stderr.decode('ascii')
                if stdout.strip() == '': raise RuntimeError("OpenCV version returned nothing!")
                elif not quiet and (cam_num==0): cprint( "\tOpenCV Version: "+stdout.strip(), 'green')
                if not quiet: print("\t",cam_num,':',stderr.strip())

                if ('out device of bound' in stderr) or ('VIDEOIO ERROR' in stderr) or ('HIGHGUI ERROR' in stderr)\
                    or ('Cannot identify device' in stderr):
                    break
        
            if ('is not a capture device' in stderr) or ('can\'t open camera by index' in stderr):
                pass
            else:
                    validCamRange.append( cam_num )    

            # only one camera anyway:
            if len(validCamRange)==1:
                if not quiet: print("Using camera %i (default)" % validCamRange[0])
                self.params['ID']=validCamRange[0]
                confirmkb=''
            else:
                user_choose_stream(validCamRange)
                confirmkb='n'  
        

        # End camera id block

        # Try to open camera stream.
        # This should cause the REC light to come on the camera if it has one.
        self.opencvdev = cv2.VideoCapture(self.params['ID'])
        
        # If user chose, check that they are happy with their choice.
        while 'n' in confirmkb:
            if self.userChoseStream and not quiet:
                cprint( "\tWebcam is now active, record light should be ON if it has one.", 'green', attrs=['bold'])
                confirmkb = input("\tIs camera correct? [Y/n] ").lower().strip()
                if 'n' in confirmkb: user_choose_stream(validCamRange)
        
        # Set up configuration for number of frames to capture per query event
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

        # Check
        try:
            assert(self.opencvdev)
            if self.opencvdev is None: raise pyLabDataLoggerIOError
        except:
            cprint( "Connection to the device is not open.", 'red', attrs=['bold'])

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

        # Get Image(s)
        self.lastValue = []
        for j in range(self.config['n_frames']):
            ret, frame = self.opencvdev.read()
            self.frame_counter += 1 # increment counter even if image not returned
            if ret:
                self.lastValue.append(frame[...])
                # Set up live preview mode if requested
                if j==0 and self.live_preview:
                    cprint("\tlive_preview: displaying frame_%08i" % self.frame_counter, 'green')
                    cv2.imshow('pyLabDataLogger: %s' % (self.params['name']),frame)
                    if cv2.waitKey(1000) & 0xFF == ord('q'): break  # require a 1000ms wait
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

