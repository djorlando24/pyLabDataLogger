"""
    Sigrok-USB device class for pyPiDataLogger
    
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

    Changelog:
        20/12/2020 : python3 support
        27/12/2020 : python3 bug fixes and buffering bug fixes for fx2lafw
        13/01/2021 : python3 serial encoding/decoding bug fixes
"""

from .device import device
from .device import pyLabDataLoggerIOError
import numpy as np
from termcolor import cprint

try:
    import usb.core
except ImportError:
    cprint( "Please install pyUSB", 'red', attrs=['bold'])
    raise

try:
    import sigrok.core.classes as sr
except ImportError:
    cprint( "Please install sigrok with Python bindings", 'red', attrs=['bold'])
    raise



class srdevice(device):
    """ Class defining a USB device that communicates via sigrok
        (which must be seperately installed).
        
        The driver is specified by 'sigrok/device' where 'device' is the name of the sigrok driver for the specific hardware.
        You can find out what sigrok supports by running
        
            sigrok-cli -L
            
        
        These are continually being added to as time progresses. As of Feb 2019 the following devices & protocols are suppored:
          ac97                 Audio Codec '97
          ade77xx              Analog Devices ADE77xx
          adf435x              Analog Devices ADF4350/1
          adns5020             Avago ADNS-5020
          am230x               Aosong AM230x/DHTxx/RHTxx
          amulet_ascii         Amulet LCD ASCII
          arm_etmv3            ARM Embedded Trace Macroblock v3
          arm_itm              ARM Instrumentation Trace Macroblock
          arm_tpiu             ARM Trace Port Interface Unit
          atsha204a            Microchip ATSHA204A
          aud                  Advanced User Debugger
          avr_isp              AVR In-System Programming
          avr_pdi              Atmel Program and Debug Interface
          can                  Controller Area Network
          cc1101               Texas Instruments CC1101
          cec                  HDMI-CEC
          cfp                  100 Gigabit C form-factor pluggable
          counter              Edge counter
          dali                 Digital Addressable Lighting Interface
          dcf77                DCF77 time protocol
          dmx512               Digital MultipleX 512
          ds1307               Dallas DS1307
          ds2408               Maxim DS2408
          ds243x               Maxim DS2432/3
          ds28ea00             Maxim DS28EA00 1-Wire digital thermometer
          dsi                  Digital Serial Interface
          edid                 Extended Display Identification Data
          eeprom24xx           24xx I²C EEPROM
          eeprom93xx           93xx Microwire EEPROM
          em4100               RFID EM4100
          em4305               RFID EM4205/EM4305
          enc28j60             Microchip ENC28J60
          flexray              FlexRay
          gpib                 General Purpose Interface Bus
          graycode             Gray code and rotary encoder
          guess_bitrate        Guess bitrate/baudrate
          hdcp                 HDCP over HDMI
          i2c                  Inter-Integrated Circuit
          i2cdemux             I²C demultiplexer
          i2cfilter            I²C filter
          i2s                  Integrated Interchip Sound
          iec                  Commodore bus
          ieee488              IEEE-488 GPIB/HPIB/IEC
          ir_nec               IR NEC
          ir_rc5               IR RC-5
          ir_rc6               IR RC-6
          jitter               Timing jitter calculation
          jtag                 Joint Test Action Group (IEEE 1149.1)
          jtag_ejtag           Joint Test Action Group / EJTAG (MIPS)
          jtag_stm32           Joint Test Action Group / ST STM32
          lin                  Local Interconnect Network
          lm75                 National LM75
          lpc                  Low Pin Count
          maple_bus            SEGA Maple bus
          max7219              Maxim MAX7219/MAX7221
          mcs48                Intel MCS-48
          mdio                 Management Data Input/Output
          microwire            Microwire
          midi                 Musical Instrument Digital Interface
          miller               Miller encoding
          mlx90614             Melexis MLX90614
          modbus               Modbus RTU over RS232/RS485
          morse                Morse code
          mrf24j40             Microchip MRF24J40
          mxc6225xu            MEMSIC MXC6225XU
          nes_gamepad          Nintendo Entertainment System gamepad
          nrf24l01             Nordic Semiconductor nRF24L01(+)
          nunchuk              Nintendo Wii Nunchuk
          onewire_link         1-Wire serial communication bus (link layer)
          onewire_network      1-Wire serial communication bus (network layer)
          ook                  On-off keying
          ook_oregon           Oregon Scientific
          ook_vis              On-off keying visualisation
          pan1321              Panasonic PAN1321
          parallel             Parallel sync bus
          pca9571              NXP PCA9571
          ps2                  PS/2
          pwm                  Pulse-width modulation
          qi                   Qi charger protocol
          rc_encode            Remote control encoder
          rfm12                HopeRF RFM12
          rgb_led_spi          RGB LED string decoder (SPI)
          rgb_led_ws281x       RGB LED string decoder (WS281x)
          rtc8564              Epson RTC-8564 JE/NB
          sda2506              Siemens SDA 2506-5
          sdcard_sd            Secure Digital card (SD mode)
          sdcard_spi           Secure Digital card (SPI mode)
          seven_segment        7-segment display
          signature            Signature analysis
          spdif                Sony/Philips Digital Interface Format
          spi                  Serial Peripheral Interface
          spiflash             SPI flash/EEPROM chips
          ssi32                Synchronous Serial Interface (32bit)
          st7735               Sitronix ST7735
          stepper_motor        Stepper motor position / speed
          swd                  Serial Wire Debug
          swim                 STM8 SWIM bus
          t55xx                RFID T55xx
          tca6408a             Texas Instruments TCA6408A
          tdm_audio            Time division multiplex audio
          timing               Timing calculation with frequency and averaging
          tlc5620              Texas Instruments TLC5620
          uart                 Universal Asynchronous Receiver/Transmitter
          usb_packet           Universal Serial Bus (LS/FS) packet
          usb_power_delivery   USB Power Delivery
          usb_request          Universal Serial Bus (LS/FS) transaction/request
          usb_signalling       Universal Serial Bus (LS/FS) signalling
          wiegand              Wiegand interface
          x2444m               Xicor X2444M/P
          xfp                  10 Gigabit Small Form Factor Pluggable Module (XFP)
          z80                  Zilog Z80 CPU
    """

    def __init__(self,params={},quiet=True,**kwargs):
        
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
            if not self.quiet: cprint( '\tSample rate must be set on the oscilloscope in advance', 'yellow')
            self.config['valid_samplerates']=(1,)
        else:
            if not self.quiet: cprint( '\tDefault samplerates not known for %s' % self.params['model'],'yellow')
            self.config['valid_samplerates']=(1,)
        
        self.config['samplerate']=self.config['valid_samplerates'][0]
    
    # Callback for sigrok logging (for debug mode)
    def log_callback_debug(self, loglevel, s):  
        if self.quiet: return
        if loglevel != sr.LogLevel.SPEW:
            print( "\t\tsr(%s): %s" % (loglevel, repr(s)) )
        return

    # Callback for sigrok logging (for normal operation mode)
    def log_callback_normal(self, loglevel, s):
        if self.quiet: return
        if loglevel == sr.LogLevel.INFO:
            print( "\t\tsr(%s): %s" % (loglevel, repr(s)) )
        return

    # Establish connection to device (ie open port)
    def activate(self):
        if self.driver != 'sigrok':
            raise ValueError("Cannot use driver %s with sigrokUsbDevice" % self.driver)
            
        # Make new Sigrok context, attempt to load driver requested.
        cprint( "\tconnecting to %s - sigrok driver" % self.name ,'green')
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
        self.sessionReady = 0 # Zero when session not yet created, 1 when created, >1 when good to go
        self.has_digital_input = False
                
        if not self.quiet: print( "\t%s - %s with %d channels: %s" % (self.srdev.driver.name, str.join(' ',\
                [s for s in (self.srdev.vendor, self.srdev.model, self.srdev.version) if s]),\
                len(self.srdev.channels), str.join(' ', [c.name for c in self.srdev.channels])) )

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
                print( "\tEnabled channels:",[self.config['channel_names'][i] for i in range(nch) if self.config['enabled'][i]])
        self.default_samplerate()
        
        # Set default configuration parameters
        if not 'n_samples' in self.config.keys(): self.config['n_samples']=8
        self.params['n_channels']=len(self.srdev.channels)
        self.apply_config()
               
        # Run one set of samples to update raw_units and check connection is good.
        self.query()
        if not self.quiet: self.pprint()
        
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
                        cprint( "Samplerate %s not accepted" % self.config['samplerate'], 'red', attrs=['bold'])
                        cprint( "Valid sample rates = %s " % self.config['valid_samplerates'], 'red', attrs=['bold'])
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


    # Sigrok datafeed_in subroutine
    def datafeed_in(self, device, packet):
        if self.has_digital_input: self.data_buffer[1] += self.srdoutput.receive(packet)
        self.data_buffer[0] += self.sraoutput.receive(packet)
        return None

    
    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        
        if self.sessionReady <= 0:
            if self.debugMode: print("\tCreating sigrok session")
            #if not 'srsession' in dir(self):
            self.srsession = self.srcontext.create_session()
            self.srsession.add_device(self.srdev)           
            self.srsession.start()
            self.sessionReady = 1            
        
            if self.has_digital_input: 
                #if not 'srdoutput' in dir(self):
                self.srdoutput = self.srcontext.output_formats['bits'].create_output(self.srdev)
            
            #if not 'sraoutput' in dir(self):
            self.sraoutput = self.srcontext.output_formats['analog'].create_output(self.srdev)
            self.srsession.add_datafeed_callback(self.datafeed_in)
            self.sessionReady = 2

        assert self.sraoutput, self.srsession
        if self.has_digital_input: assert self.srdoutput        
        
        try:
            
            # Sample
            self.data_buffer = ['', '']
            if self.sessionReady<2: 
                self.srsession.start()
                self.sessionReady=2
            
            self.srsession.run()
            self.updateTimestamp()
            self.srsession.stop()
            self.sessionReady = 1
                                    
            #if self.has_digital_input:
            #    del self.srdoutput
            #del self.sraoutput
            #del self.srsession
            #self.sessionReady = 0
            
            # Parse analog values - get buffer
            #if self.debugMode: print('\tOutput buffer =',self.data_buffer)
            delimited_buffer = self.data_buffer[0].split('\n')

            if self.data_buffer == ['', '']: raise pyLabDataLoggerIOError

            if 'enabled' in self.config:
                n_analog_channels = np.sum(self.config['enabled']) - sum(self.params['sr_logic_channel'])
            else:
                n_analog_channels = np.sum(self.params['n_channels']) - sum(self.params['sr_logic_channel']) 

            # Make list of empty lists to put values in.
            # initialize raw_units to empty strings.
            self.lastValue = [[]] * n_analog_channels
            self.params['raw_units'] = [[]] * n_analog_channels
            
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
                self.config['eng_units'] = self.params['raw_units']
            if len(self.config['eng_units']) != len(self.params['raw_units']):
                self.config['eng_units'] = self.params['raw_units']

            # Put in NaN if buffer under-full or empty
            if len(delimited_buffer[0]) == 0:
                self.lastValue = [[np.nan]]*n_analog_channels
                self.params['raw_units'] = ['']*n_analog_channels
            if [] in self.lastValue:
                for n in range(len(self.lastValue)):
                    if self.lastValue[n]==[]: self.lastValue[n]=[np.nan]              

            # Parse binary data
            if self.has_digital_input:
                digital_data = [[]]*sum(self.params['sr_logic_channel'])
                j=0
                for dch in self.data_buffer[1].split('\n'):
                    if ('D' in dch) and (j<len(digital_data)):
                        # The input is something like D0:010 for 3 samples of D0.
                        # We can break it apart with the list() function and then
                        # run thru a list comprehension to convert to ints.
                        digital_data[j] = [ int(val) for val in list(dch.split(':')[1:][0].replace(' ','')) ]
                        j+=1

                # Assume digital channels always come first in mixed mode devices?
                self.lastValue = digital_data + self.lastValue
                self.params['raw_units'] = ['']*len(digital_data) + self.params['raw_units']
                self.config['eng_units'] = ['']*len(digital_data) + self.config['eng_units']
                    

            # If only 1 sample, convert self.lastValue to list rather than list of lists with 1 item each.
            if self.config['n_samples']<=1:
                self.lastValue = np.array([ v[-1] for v in self.lastValue ])
                #print( '%s %s' % (self.lastValue, self.params['raw_units'] ) )

                # Convert analog values to scaled values
                self.lastScaled=self.lastValue * self.config['scale'] + self.config['offset']
            
            lengths=[len(v) for v in self.lastValue]
            if len(set(lengths)) > 1:
                # What to do if the number of samples for each var is mis-matched.
                # This can happen if libsigrok keeps prior samples from digital channels in its buffer.
                # Take the last min_samples number of values (# analog vals or n_samples whichever less).
                min_samples = min(lengths)
                if min_samples>self.config['n_samples']: min_samples=self.config['n_samples']
                for j in range(len(self.lastValue)):
                    self.lastValue[j] = self.lastValue[j][-min_samples:]

            if self.config['n_samples']>1:
                # Convert analog values to scaled values - multi samples
                self.lastValue = np.array(self.lastValue)
                self.lastScaled = [ np.array(self.lastValue[j])*self.config['scale'][j] + self.config['offset'][j] for j in range(len(self.lastValue)) ]
            

        except pyLabDataLoggerIOError:
            cprint( "Unable to communicate with %s"  % self.name, 'red', attrs=['bold'])
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

