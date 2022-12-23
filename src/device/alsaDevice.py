"""
    ALSA audio capture device class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2023 LTRAC
    @license GPL-3.0+
    @version 1.3.0
    @date 23/12/2022
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

    TODO: need to test with known function to ensure stereo encoding and bit depth unpacking is correct.

"""

from .device import device
from .device import pyLabDataLoggerIOError
import numpy as np
import datetime, time
from termcolor import cprint

try:
    import alsaaudio
except ImportError:
    cprint( "Please install pyalsaaudio module/", 'red', attrs=['bold'])
    raise

try:
    import usb.core
except ImportError:
    cprint( "Please install pyUSB", 'red', attrs=['bold'])
    raise

########################################################################################################################
class alsaDevice(device):
    """ Class providing support for ...
    """

    def __init__(self,params={},quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        if 'debugMode' in kwargs.keys(): self.debugMode = kwargs['debugMode']
        else: self.debugMode=False
        
        if 'card' in kwargs.keys(): self.alsacard = kwargs['card']
        elif 'card' in params.keys(): self.alsacard = self.params['card']
        else: self.alsacard=None
        
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet

        # Set attribute defaults to Mono, 44100 Hz
        if not 'channels' in self.params: self.params['channels']=1
        self.params['n_channels'] = self.params['channels']
        if not 'samplerate' in self.params: self.params['samplerate']=44100
        
        if params is not {}: self.scan(quiet=self.quiet)
        
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
            raise pyLabDataLoggerIOError("USB Device %s not found" % self.params['name'])

        #print usbCoreDev.bus, usbCoreDev.address

        if self.alsacard is not None:
            if not self.alsacard in alsaaudio.card_indexes():
                raise IndexError("Invalid ALSA card number requested.")
        else:
            
            # Scan ALSA devices
            if 'card_indexes' in dir(alsaaudio):
                cards = [ (n, ' '.join(alsaaudio.card_name(n))) for n in alsaaudio.card_indexes() ]
            elif 'cards' in dir(alsaaudio):
                cards = [ (n, alsaaudio.cards()[n]) for n in range(len(alsaaudio.cards())) ]
            else:
                raise RuntimeError("Unknown alsaaudio API:\n"+dir(alsaaudio))
            #if self.debugMode: print "\tAll ALSA devices:",alsaaudio.cards()
            
            #  find one that matches the USB device found.
            if any(['USB' in c[1] for c in cards]): # if 'USB' in the name of any device, select from those
                cards = [ c for c in cards if 'USB' in c[1] ]
            if len(cards)==0:
                cprint( "\tUnable to find a USB ALSA device.", 'red', attrs=['bold'])
                # abort setup.
                return
            elif len(cards)==1:
                cprint( "\tFound 1 USB ALSA card: [card %02i] %s" % cards[0], 'green')
                self.alsacard = cards[0][0]
                self.name = "ALSA Audio device "+cards[0][1]
            elif len(cards)>1:
                print( "\tFound multiple ALSA cards. The first one may be your internet sound card." )
                print( "\tPlease choose one of:" )
                for j in range(len(cards)): print("\t\t%i: [card %02i] %s" % (j,cards[j][0], cards[j][1]))
                j=-1
                while (j<0) or (j>=len(cards)):
                    try: j=int(input("Choose audio stream [0-%i]:" % (len(cards)-1)))
                    except KeyboardInterrupt: exit(1)
                    except: pass
                self.alsacard = cards[j][0]
                self.name = "ALSA Audio device "+cards[j][1]
        
        
        if self.alsacard: self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):

        # Attempt to open the device in non-blocking capture mode
        # arguments depends on alsaaudio version.
        try:
            self.pcm = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, cardindex=self.alsacard)
        except TypeError:
            self.pcm = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK) # default card
        
        # Set up as requested
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

        cprint( "\tSettings: %i channels @ %.0f Hz / %i bits, sampling for %f sec" %\
              (self.params['channels'],self.params['samplerate'],self.params['bitdepth'],self.params['sampleperiod']) , 'green' )
        
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
            if self.deviceClass is None: raise pyLabDataLoggerIOError("Could not access PCM device")
            
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
            assert(self.pcm)
            if self.pcm is None: raise pyLabDataLoggerIOError("Could not access PCM device")
        except:
            cprint( "Connection to the ALSA PCM device is not open.", 'red', attrs=['bold'])

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
                if self.lastValue[chi] is None: print("\t%s - empty" % self.config['channel_names'][chi])
                else: print("\t%s - %i samples captured (%g sec)" % \
                    (self.config['channel_names'][chi],len(self.lastValue[chi]),\
                     float(len(self.lastValue[chi])/float(self.params['samplerate']))))

        
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


