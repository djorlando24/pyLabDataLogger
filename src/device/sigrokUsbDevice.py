"""
    Sigrok-USB device class for pyPiDataLogger
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 27/02/2019
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

try:
    import usb.core
except ImportError:
    print "Please install pyUSB"
    raise

try:
    import sigrok.core.classes as sr
except ImportError:
    print "Please install sigrok with Python bindings"
    raise



class srdevice(device):
    """ Class defining a USB device that communicates via sigrok
        (which must be seperately installed).
    """

    def __init__(self,params={},quiet=False,**kwargs):
        
        # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.config = {}
        
        # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.params = params
        self.driver = None
        self.driverConnected = False # Goes to True when scan method succeeds
        
        self.name = "untitled USB device"
        
        self.lastValue = None # Last known value (for logging)
        
        self.lastValueTimestamp = None # Time when last value was obtained
        
        self.subdriver = self.params['driver'].lower().split('/')[1]

        if 'debugMode' in kwargs: self.debugMode=kwargs['debugMode']
        else: self.debugMode=False

        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet

        if params is not {}:
            self.scan()
            self.activate()
        
        return

    # Detect if device is present
    def scan(self,override_params=None):
        if override_params is not None: self.params = override_params
        
        # Check device is present on the bus.
        if 'bcdDevice' in self.params.keys():
            usbCoreDev = usb.core.find(idVendor=self.params['vid'],idProduct=self.params['pid'],\
                             bcdDevice=self.params['bcdDevice'])
        else:
            usbCoreDev = usb.core.find(idVendor=self.params['vid'],idProduct=self.params['pid'])
            
        if usbCoreDev is None:
            raise pyLabDataLoggerIOError("USB Device %s not found" % self.params['name'])

        # Parse driver parameters
        self.driver = self.params['driver'].lower().split('/')[0]
        self.bus = usbCoreDev.bus
        self.adds = usbCoreDev.address
        self.name = self.params['name']
        return


    # Define default and possible sample rates on activation
    def default_samplerate(self):
        if self.params['model'] == 'USBee AX':        # LHT00SU1
            self.config['valid_samplerates']=(20000,25000,50000,100000,200000,250000,500000,\
                                            1000000,2000000,3000000,4000000,6000000,8000000,\
                                            12000000,16000000,24000000)
        elif (self.params['model'] == 'UT32x') or (self.params['model'] == '72-7730'):
            self.config['valid_samplerates']=(None,)
        elif self.subdriver == 'rigol-ds':
            if not self.quiet: print '\tSample rate must be set on the oscilloscope in advance'
            self.config['valid_samplerates']=(1,)
        else:
            if not self.quiet: print '\tDefault samplerates not known for',self.params['model']
            self.config['valid_samplerates']=(1,)
        
        self.config['samplerate']=self.config['valid_samplerates'][0]
    
    # Callback for sigrok logging (for debug mode)
    def log_callback_debug(self, loglevel, s):  
        if self.quiet: return
        if loglevel != sr.LogLevel.SPEW:
            print "\t\tsr(%s):" % loglevel, repr(s)
        return

    # Callback for sigrok logging (for normal operation mode)
    def log_callback_normal(self, loglevel, s):
        if self.quiet: return
        if loglevel == sr.LogLevel.INFO:
            print "\t\tsr(%s):" % loglevel, repr(s)
        return

    # Establish connection to device (ie open port)
    def activate(self):
        if self.driver != 'sigrok':
            raise ValueError("Cannot use driver %s with sigrokUsbDevice" % self.driver)
            
        # Make new Sigrok context, attempt to load driver requested.
        print "\tconnecting to %s - sigrok driver" % self.name
        self.srcontext = sr.Context.create()
        if self.debugMode: self.srcontext.set_log_callback(self.log_callback_debug) # noisy debugging
        else: self.srcontext.set_log_callback(self.log_callback_normal) # minimal messages
        srdriver = self.srcontext.drivers[self.subdriver]
        if self.subdriver == 'rigol-ds':
            srdevs = srdriver.scan()  # Only one Rigol DS scope can be used at a time
        else:
            srdevs = srdriver.scan(conn='%i.%i' % (self.bus, self.adds)) # find by address in case of multiple devices
        if len(srdevs) == 0: raise pyLabDataLoggerIOError("\tsigrok unable to communicate with device %s." % self.name)
        
        # Set up sigrok device
        self.srdev = srdevs[0]
        self.params['model']=self.srdev.model
        self.params['vendor']=self.srdev.vendor
        self.params['version']=self.srdev.version
        self.params['raw_units'] = []
        self.srdev.open()
        self.driverConnected = True
        self.sessionReady = 0 # Zero when session not yet created, 1 when created by callback not setup, 2 when good to go.
        self.has_digital_input = False
                
        if not self.quiet: print "\t%s - %s with %d channels: %s" % (self.srdev.driver.name, str.join(' ',\
                [s for s in (self.srdev.vendor, self.srdev.model, self.srdev.version) if s]),\
                len(self.srdev.channels), str.join(' ', [c.name for c in self.srdev.channels]))

        # Determine channel types and names.
        if sr.ChannelType.LOGIC in [c.type for c in self.srdev.channels]:
            #self.config['channel_names'] = [c.name for c in self.srdev.channels if c.type!=sr.ChannelType.LOGIC]
            #self.params['sr_channels'] = [c for c in self.srdev.channels if c.type!=sr.ChannelType.LOGIC]
            #self.config['channel_names'].append('Digital Input')
            #self.params['sr_channels'].append([c for c in self.srdev.channels if c.type==sr.ChannelType.LOGIC])
            #self.params['raw_units'].append('')
            self.has_digital_input = True

        self.config['channel_names'] = [c.name for c in self.srdev.channels]
        self.params['sr_channels'] = [c for c in self.srdev.channels]
        self.params['sr_logic_channel'] = [c.type == sr.ChannelType.LOGIC for c in self.srdev.channels]
        
        # Set parameters
        nch=len(self.config['channel_names'])
        self.params['n_channels']=nch
        self.config['scale'] = np.ones(nch,)
        self.config['offset'] = np.zeros(nch,)
        self.config['enabled'] = [c.enabled for c in self.srdev.channels]
        if False in self.config['enabled']: 
            if not self.quiet: 
                print "\tEnabled channels:",[self.config['channel_names'][i] for i in range(nch) if self.config['enabled'][i]]
        self.default_samplerate()
        
        # Set default configuration parameters
        if not 'n_samples' in self.config.keys(): self.config['n_samples']=1
        self.params['n_channels']=len(self.srdev.channels)
        self.apply_config()
               
        # Run one set of samples to update raw_units and check connection is good.
        self.query()
        self.pprint()
        
        return


    # Apply configuration changes from self.config to the underlying driver.
    def apply_config(self):

        # Set num samples / frames
        if self.subdriver == 'rigol-ds':
            # Oscilloscopes use frames
            self.srdev.config_set(sr.ConfigKey.LIMIT_FRAMES,  int(self.config['n_samples']))
        else:
            # Other devices use samples
            self.srdev.config_set(sr.ConfigKey.LIMIT_SAMPLES, int(self.config['n_samples']))
        
        for i in range(len(self.params['sr_channels'])):
            if isinstance( self.params['sr_channels'][i], list):
                for ch in self.params['sr_channels'][i]: ch.enable = self.config['enabled'][i]
            else:
                self.params['sr_channels'][i].enable = self.config['enabled'][i]
    
        # Set samplerate if reqiured (not supported on Rigol DS)
        if self.subdriver != 'rigol-ds':
            if self.config['valid_samplerates'][0] is not None:
                try:
                    if not self.config['samplerate'] in self.config['valid_samplerates']:
                        print "Samplerate",self.config['samplerate'],"not accepted"
                        print "Valid sample rates =",self.config['valid_samplerates']
                    self.srdev.config_set(sr.ConfigKey.SAMPLERATE, self.config['samplerate'])
                except ValueError as err:
                    pass
    
        return

    

    # Deactivate connection to device (ie close serial port)
    def deactivate(self):
        self.close()
        del self.srdev, self.srcontext
        self.driverConnected=False
        return


    
    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        
        if self.sessionReady<1:
            self.srsession = self.srcontext.create_session()
            self.srsession.add_device(self.srdev)
            self.srsession.start()
        
            if self.has_digital_input:
                self.srdoutput = self.srcontext.output_formats['bits'].create_output(self.srdev)
            self.sraoutput = self.srcontext.output_formats['analog'].create_output(self.srdev)

            self.sessionReady = 1

        assert self.sraoutput, self.srsession
        if self.has_digital_input: assert self.srdoutput
    
        def datafeed_in(device, packet):
            if self.has_digital_input: self.data_buffer[1] += self.srdoutput.receive(packet)
            self.data_buffer[0] += self.sraoutput.receive(packet)
            return None
        
        try:
            if self.sessionReady < 2:
                self.srsession.add_datafeed_callback(datafeed_in)
                self.sessionReady = 2
            
            # Sample
            self.data_buffer = ['', '']  
            self.srsession.run()
            self.updateTimestamp()
            self.srsession.stop()
            
            # Parse analog values - get buffer
            #if self.debugMode: print '\tOutput buffer =',self.data_buffer
            delimited_buffer = self.data_buffer[0].split('\n')
            if 'enabled' in self.config:
                n_analog_channels = np.sum(self.config['enabled']) - sum(self.params['sr_logic_channel'])
            else:
                n_analog_channels = np.sum(self.params['n_channels']) - sum(self.params['sr_logic_channel']) 

            # Make list of empty lists to put values in.
            # initialize raw_units to empty strings.
            self.lastValue = []; self.params['raw_units'] = []
            for i in range(n_analog_channels):
                self.lastValue.append([])
                self.params['raw_units'].append('')
            
            # Loop thru buffer entries
            n = 0
            for aVal in delimited_buffer:
                if len(aVal) >0:
                    s=aVal.strip(':').split(' ')
                   
                    if not 'FRAME-END' in aVal:
                        self.lastValue[n].append(float(s[1])) # save value
                        self.params['raw_units'][n] = ' '.join(s[2:]).strip() # save unit
                        n = (n+1)%n_analog_channels               


            # Check existence of eng_units
            if not 'eng_units' in self.config:
                self.params['eng_units'] = self.params['raw_units']
            if len(self.params['eng_units']) != len(self.params['raw_units']):
                self.params['eng_units'] = self.params['raw_units']

            # Put in NaN if buffer under-full or empty
            if len(delimited_buffer[0]) == 0:
                self.lastValue = [[np.nan]]*n_analog_channels
                self.params['raw_units'] = ['']*n_analog_channels
            if [] in self.lastValue:
                for n in range(len(self.lastValue)):
                    if self.lastValue[n]==[]: self.lastValue[n]=[np.nan]              

            # Parse binary data
            if self.has_digital_input:
                digital_data = []
                for dch in self.data_buffer[1].split('\n')[2:]:
                    if dch != '':
                        # The input is something like D0:010 for 3 samples of D0.
                        # We can break it apart with the list() function and then
                        # run thru a list comprehension to convert to ints.
                        digital_data.append( [int(val) for val in list(dch.split(':')[1:][0].replace(' ','')) ] )
            
                # Assume digital channels always come first in mixed mode devices?
                self.lastValue = digital_data + self.lastValue
                self.params['raw_units'] = ['']*len(digital_data) + self.params['raw_units']
          
            # Convert analog values to scaled values
            for t in range(self.config['n_samples']):
                self.lastScaled = np.array(self.lastValue)[:,t] * self.config['scale'] + self.config['offset']

            # If only 1 sample, convert self.lastValue to list rather than list of lists with 1 item each.
            if self.config['n_samples']<2:
                self.lastValue = [ v[0] for v in self.lastValue ]
                print self.lastValue, self.params['raw_units']

        except pyLabDataLoggerIOError:
            print "Unable to communicate with %s"  % self.name
            self.lastValue=[np.nan]*self.params['n_channels']


        # Expand the length of units and lastValue and lastScaled if not all channels are enabled.
        if (len(self.lastValue)<self.params['n_channels']) and ('enabled' in self.config):
            idx = []; n=0
            for c in self.config['enabled']:
                if c==1: 
                    idx.append(n)
                    n+=1
                else: idx.append(None)
            lastValue=[]
            lastScaled=[]
            raw_units=[]
            for n in idx:
                if n is None: 
                    lastValue.append(np.nan)
                    lastScaled.append(np.nan)
                    raw_units.append('')
                else:
                    lastValue.append(self.lastValue[n])
                    lastScaled.append(self.lastScaled[n])
                    raw_units.append(self.params['raw_units'][n])
            self.lastValue = lastValue
            self.lastScaled = lastScaled
            self.params['raw_units'] = raw_units

        return self.lastValue

