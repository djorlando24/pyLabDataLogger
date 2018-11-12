"""
    ALSA audio capture device class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 23/10/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    TODO: need to test with known function to ensure stereo encoding and bit depth unpacking is correct.

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
                print "\tFound 1 USB ALSA card: [card %02i] %s" % cards[0]
                self.alsacard = cards[0][0]
                self.name = cards[0][1]
            elif len(cards)>1:
                print "\tFound multiple ALSA cards:"
                for c in cards: print "\t\t[card %02i] %s" % c
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
       
        # Set attributes. Default is Mono, 44100 Hz
        if not 'channels' in self.params: self.params['channels']=1
        if not 'samplerate' in self.params: self.params['samplerate']=44100
        self.pcm.setchannels(self.params['channels'])
        self.pcm.setrate(self.params['samplerate'])

        # Set encoding of samples. default is 16 bit little endian samples.
        # depends on what PCM device can support.
        if not 'bitdepth' in self.params: self.params['bitdepth']=16
        if self.params['bitdepth']==8: 
            self.pcm.setformat(alsaaudio.PCM_FORMAT_S8_LE)
            self.params['dtype']='<i1' # '<b'
        elif self.params['bitdepth']==16: 
            self.pcm.setformat(alsaaudio.PCM_FORMAT_S16_LE)
            self.params['dtype']='<i2'# '<h'
        elif self.params['bitdepth']==24: 
            self.pcm.setformat(alsaaudio.PCM_FORMAT_S24_LE)
            self.params['dtype']='<i3'
        else: raise ValueError( "\tError - unsupported bitdepth %i " % self.params['bitdepth'] )
        self.pcm.setformat(alsaaudio.PCM_FORMAT_S16_LE)

        if not 'sampleperiod' in self.params: self.params['sampleperiod']=0.1

        print "\tSettings: %i channels @ %.0f Hz / %i bits, sampling for %f sec" %\
              (self.params['channels'],self.params['samplerate'],self.params['bitdepth'],self.params['sampleperiod'])
        
        # The period size controls the internal number of frames per period.
        # The significance of this parameter is documented in the ALSA api.
        # For our purposes, it is suficcient to know that reads from the device
        # will return this many frames. Each frame being 2 bytes long.
        # This means that the reads below will return either 320 bytes of data
        # or 0 bytes of data. The latter is possible because we are in nonblocking
        # mode.
        self.params['pcm_periodsize']=160
        self.pcm.setperiodsize(self.params['pcm_periodsize'])
        
        # Required config and params for pyLabDataLogger...
        self.config['channel_names']=['Ch%02i' % i for i in range(self.params['channels'])]
        self.params['raw_units']=['']*self.params['channels']
        self.config['eng_units']=['']*self.params['channels']
        self.config['scale']=np.array([1.]*self.params['channels'])
        self.config['offset']=np.array([0.]*self.params['channels'])
        self.params['n_channels']=self.params['channels']
        
        self.driverConnected=True
        
        # Make first query
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        self.pcm.close()
        self.driverConnected=False
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
            assert(self.pcm)
            if self.pcm is None: raise IOError
        except:
            print "Connection to the ALSA PCM device is not open."

        # Make empty output
        self.lastValue = [None]*self.params['n_channels']

        # Read values
        # Determine num frames to read:
        loops = int(self.params['sampleperiod']*self.params['samplerate']*self.params['n_channels'])/self.params['pcm_periodsize']
        while loops > 0:
            l, data = self.pcm.read() # read from device
            if l: 
                loops -= 1 #; time.sleep(.001)
                values = np.fromstring(data, dtype=self.params['dtype']) # unpack
                for chi in range(self.params['n_channels']): # loop ch's
                    # assume stereo encoding is interleaved; [ L R L R ] etc.
                    if self.lastValue[chi] is None: self.lastValue[chi]=values[chi::self.params['n_channels']].copy()
                    else: self.lastValue[chi] = np.hstack(( self.lastValue[chi], values[chi::self.params['n_channels']] ))

        # Give some diagnostics on the first time after a reset.
        if reset:
            for chi in range(self.params['n_channels']):
                if self.lastValue[chi] is None: print "\t%s - empty" % self.config['channel_names'][chi]
                else: print "\t%s - %i samples captured (%g sec)" % \
                    (self.config['channel_names'][chi],len(self.lastValue[chi]),\
                     float(len(self.lastValue[chi])/float(self.params['samplerate'])))

        
        if np.all(self.config['scale']==1.) and np.all(self.config['offset']==0.):
            # No scaling
            self.lastScaled = self.lastValue
        else:
            # Generate scaled values. Convert non-numerics to NaN
            lastValueSanitized = []
            for v in self.lastValue: 
                if v is None: lastValueSanitized.append(np.nan)
                else: lastValueSanitized.append(v)

            self.lastScaled = [None]*self.params['n_channels']
            for chi in range(self.params['n_channels']):
                self.lastScaled[chi] = np.array(lastValueSanitized[chi]) * self.config['scale'][chi] + self.config['offset'][chi]
        
        self.updateTimestamp()
        return self.lastValue

