"""
    Sigrok-USB device class for pyPiDataLogger
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 11/10/2018
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

try:
    import usb.core
except ImportError:
    print "Please install pyUSB"
    raise


class srdevice(device):
    """ Class defining a USB device that communicates via sigrok
        (which must be seperately installed).
    """

    def __init__(self,params={}):
        
        # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.config = {}
        
        # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.params = params
        self.driver = None
        self.driverConnected = False # Goes to True when scan method succeeds
        
        self.name = "untitled USB device"
        
        self.lastValue = None # Last known value (for logging)
        
        self.lastValueTimestamp = None # Time when last value was obtained
        
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
            raise IOError("USB Device %s not found" % self.params['name'])

        # Parse driver parameters
        self.driver = self.params['driver'].lower().split('/')[0]
        self.bus = usbCoreDev.bus
        self.adds = usbCoreDev.address
        self.name = self.params['name']
        return


    # Define default and possible sample rates on activation
    def default_samplerate(self):
        # LHT00SU1
        if self.params['model'] == 'USBee AX':
            self.config['valid_samplerates']=(20000,25000,50000,100000,200000,250000,500000,\
                                            1000000,2000000,3000000,4000000,6000000,8000000,\
                                            12000000,16000000,24000000)
        else:
            self.config['valid_samplerates']=(1,)
        
        self.config['samplerate']=self.config['valid_samplerates'][0]
    


    # Establish connection to device (ie open port)
    def activate(self):
        if self.driver != 'sigrok':
            raise ValueError("Cannot use driver %s with sigrokUsbDevice" % self.driver)
            
        # Make new Sigrok context, attempt to load driver requested.
        print "connecting to %s - sigrok driver" % self.name
        import sigrok.core.classes as sr
        self.srcontext = sr.Context.create()
        srdriver = self.srcontext.drivers[self.params['driver'].lower().split('/')[1]]
        srdevs = srdriver.scan(conn='%i.%i' % (self.bus, self.adds))
        if len(srdevs) == 0: raise IOError("Sigrok unable to communicate with device %s." % self.name)
        
        # Set up sigrok device
        self.srdev = srdevs[0]
        self.params['model']=self.srdev.model
        self.params['vendor']=self.srdev.vendor
        self.params['version']=self.srdev.version
        self.params['raw_units'] = []
        self.srdev.open()
        self.driverConnected = True
        self.has_digital_input = False
        
        print "\t%s - %s with %d channels: %s" % (self.srdev.driver.name, str.join(' ',\
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
        self.default_samplerate()
        
        # Set default configuration parameters
        if not 'n_samples' in self.config.keys(): self.config['n_samples']=1
        self.params['n_channels']=len(self.srdev.channels)
        self.apply_config()
        
        # Prepare for sampling
        self.srsession = self.srcontext.create_session()
        self.srsession.add_device(self.srdev)
        self.srsession.start()
        if self.has_digital_input:
            self.srdoutput = self.srcontext.output_formats['bits'].create_output(self.srdev)
        self.sraoutput = self.srcontext.output_formats['analog'].create_output(self.srdev)
        
        # Run one set of samples to update raw_units and check connection is good.
        self.query()
        self.pprint()
        
        return


    # Apply configuration changes from self.config to the underlying driver.
    def apply_config(self):
        import sigrok.core.classes as sr
        # Set num samples and samplate rate
        self.srdev.config_set(sr.ConfigKey.LIMIT_SAMPLES, int(self.config['n_samples']))
        
        for i in range(len(self.params['sr_channels'])):
            if isinstance( self.params['sr_channels'][i], list):
                for ch in self.params['sr_channels'][i]: ch.enable = self.config['enabled'][i]
            else:
                self.params['sr_channels'][i].enable = self.config['enabled'][i]
    
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
        import sigrok.core.classes as sr
        self.close()
        del self.srdev, self.srcontext
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
    
        try:
            assert self.sraoutput, self.srsession
            if self.has_digital_input: assert self.srdoutput
        except:
            raise
    
        def datafeed_in(device, packet):
            if self.has_digital_input: self.data_buffer[1] += self.srdoutput.receive(packet)
            self.data_buffer[0] += self.sraoutput.receive(packet)
            return None
        
        try:
            self.srsession.add_datafeed_callback(datafeed_in)
            
            # Sample
            self.data_buffer = ['', '']
            self.srsession.run()
            self.updateTimestamp()
            self.srsession.stop()
            
            # Parse analog values
            n_analog_channels = self.params['n_channels'] - sum(self.params['sr_logic_channel'])
            self.lastValue = [[]]*n_analog_channels
            self.params['raw_units'] = []       
            n = 0
            if len(''.join(self.data_buffer)) < 1: raise IOError
            
            for aVal in self.data_buffer[0].split('\n'):
                if len(aVal) >0:
                    s=aVal.strip(':').split(' ')
                    
                    self.lastValue[n].append(float(s[1]))
                    n = (n+1)%n_analog_channels
                    
                    # Update raw_units
                    #if len(self.params['raw_units']) < n_analog_channels:
                    #    self.params['raw_units'].append(s[-1].strip())
                    self.params['raw_units'].append(s[-1].strip())

                    # Check existence of eng_units
                    if not 'eng_units' in self.config:
                        self.params['eng_units'] = self.params['raw_units']
                    if len(self.params['eng_units']) != len(self.params['raw_units']):
                        self.params['eng_units'] = self.params['raw_units']
            
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

        except IOError:
            print "Unable to communicate with %s"  % self.name
            return None


        
        return self.lastValue

