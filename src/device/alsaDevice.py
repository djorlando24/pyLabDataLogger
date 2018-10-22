"""
    ALSA audio capture device class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 20/10/2018
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
    import alsaaudio
except ImportError:
    print "Please install pyalsaaudio module/"
    raise

try:
    import usb.core
except ImportError:
    print "Please install pyUSB"
    raise

########################################################################################################################
class alsaDevice(device):
    """ Class providing support for ...
    """

    def __init__(self,params={},quiet=False,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        if 'card' in kwargs.keys(): self.alsacard = kwargs['card']
        elif 'card' in params.keys(): self.alsacard = self.params['card']
        else: self.alsacard=None
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
       
        if override_params is not None: self.params = override_params
        
        # Check device is present on the bus.
        if 'bcdDevice' in self.params.keys():
            usbCoreDev = usb.core.find(idVendor=self.params['vid'],idProduct=self.params['pid'],\
                             bcdDevice=self.params['bcdDevice'])
        else:
            usbCoreDev = usb.core.find(idVendor=self.params['vid'],idProduct=self.params['pid'])

        if usbCoreDev is None:
            raise IOError("USB Device %s not found" % self.params['name'])

        #print usbCoreDev.bus, usbCoreDev.address

        if self.alsacard is not None:
            if not self.alsacard in alsaaudio.card_indexes():
                raise IndexError("Invalid ALSA card number requested.")
        else:
            # Scan ALSA devices and find one that matches the USB device found.
            cards = [ (n, ' '.join(alsaaudio.card_name(n))) for n in alsaaudio.card_indexes() ]
            cards = [ c for c in cards if 'USB' in c[1] ]
            if len(cards)==0:
                print "\tUnable to find a USB ALSA device."; return
            elif len(cards)==1:
                print "\tFound 1 USB ALSA card:",cards[0]
                self.alsacard = cards[0][0]
                self.name = cards[0][1]
            elif len(cards)>1:
                print "\tFound multiple ALSA cards:",cards
                print "\tBy default the first one will be used. Specify kwargs 'card' to choose a different one."
                j=0
                self.alsacard = cards[j][0]
                self.name = cards[j][1]
        
        
        if self.alsacard: self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):

        # Attempt to open the device in non-blocking capture mode        
        self.pcm = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, cardindex=self.alsacard)

       
        # Set attributes. Default is Mono, 44100 Hz, 16 bit little endian samples
        if not 'channels' in self.params: self.params['channels']=1
        if not 'samplerate' in self.params: self.params['samplerate']=44100
        if not 'bitdepth' in self.params: self.params['bitdepth']=16
        self.pcm.setchannels(self.params['channels'])
        self.pcm.setrate(self.params['samplerate'])
        if self.params['bitdepth']==16: self.pcm.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        elif self.params['bitdepth']==8: self.pcm.setformat(alsaaudio.PCM_FORMAT_S8_LE)
        elif self.params['bitdepth']==24: self.pcm.setformat(alsaaudio.PCM_FORMAT_S24_LE)
        else: raise ValueError( "\tError - unsupported bitdepth %i " % self.params['bitdepth'] )
        
        # The period size controls the internal number of frames per period.
        # The significance of this parameter is documented in the ALSA api.
        # For our purposes, it is suficcient to know that reads from the device
        # will return this many frames. Each frame being 2 bytes long.
        # This means that the reads below will return either 320 bytes of data
        # or 0 bytes of data. The latter is possible because we are in nonblocking
        # mode.
        self.pcm.setperiodsize(160)
        
        # Required config and params for pyLabDataLogger...
        self.config['channel_names']=['Ch%02i' % i for i in range(self.params['channels'])]
        self.params['raw_units']=['']*self.params['channels']
        self.config['eng_units']=['']*self.params['channels']
        self.config['scale']=[1.]*self.params['channels']
        self.config['offset']=[0.]*self.params['channels']
        self.params['n_channels']=self.params['channels']
        
        """        
        loops = 1000000
        while loops > 0:
            loops -= 1
            # Read data from device
            l, data = self.pcm.read()
          
            if l:
                f.write(data)
                time.sleep(.001)
        """
        
        # Make first query to get units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        self.pcm.close()
        return

    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        subdriver = self.params['driver'].split('/')[1:]
        try:
            assert(self.deviceClass)
            if self.deviceClass is None: raise IOError
            
            # Apply subdriver-specific variable writes
            if subdriver=='?':
                #...
                pass
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])

        except IOError as e:
            print "\t%s communication error" % self.name
            print "\t",e
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
            assert(self.deviceClass)
            if self.deviceClass is None: raise IOError
        except:
            print "Connection to the device is not open."

        # If first time or reset, get configuration (ie units)
        if not 'raw_units' in self.params.keys() or reset:
            driver = self.params['driver'].split('/')[1:]
            self.subdriver = driver[0].lower()
            # set self.params, self.config...

        # Read values        
        self.get_values()

        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue


