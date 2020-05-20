"""
    Serial device class - general serial port support
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 20/05/2020
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    Note on implementation of serial commands: 
     - commas denote a sequence of commands sent as quickly as possible.
     - a double-comma denotes a pause for data aquisition by the client device,
       where the delay is set by params['sample_period'].

"""

from device import device, pyLabDataLoggerIOError
import numpy as np
import datetime, time, struct, sys, os
import binascii

try:
    import serial
except ImportError:
    print "Please install pySerial"
    raise


########################################################################################################################
class serialDevice(device):
    """ Class providing support for any tty type serial device. 
        By default we assume that the ttys can be found in /dev (*nix OS)
        However this can be overridden by passing 'port' or 'tty' directly
        in the params dict.
        
        The 'serial' driver supports the following hardware:
            'serial/tds220gpib'        : Tektronix TDS22x series oscilloscopes via the RS-232 port
            'serial/omega-ir-usb'      : Omega IR-USB temperature probe with built in USB to Serial converter
            'serial/omega-usbh         : Omega USB-H 'high speed' pressure transducers with built in USB to Serial converter
            'serial/ohaus7k'           : OHAUS 7000 series scientific scales via RS232
            'serial/center310'         : CENTER 310 Temperature and Humidity meter
            'serial/tc08rs232'         : Pico TC08 RS-232 thermocouple datalogger (USB version has a seperate driver 'picotc08')
            'serial/omega-iseries/232' : Omega iSeries Process Controller via RS232 transciever
            'serial/omega-iseries/485' : Omega iSeries Process Controller via RS485 transciever
            'serial/alicat'            : Alicat Scientific M-series mass flow meter
            'serial/wtb'               : Radwag WTB precision balance/scale
    """


    def __init__(self,params={},tty_prefix='/dev/',quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.Serial = None
        self.tty_prefix = tty_prefix
        
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet
        
        self.driver = self.params['driver'].split('/')[1:]
        self.subdriver = self.driver[0].lower()
        
        if self.subdriver=='tc08rs232':
            try:
                from thermocouples_reference import thermocouples
            except ImportError:
                print "Please install the thermocouples_reference module"
                raise

        # Apply custom initial configuration settings
        if 'usbh-rate' in kwargs: self.config['RATE'] = kwargs['usbh-rate']
        if 'usbh-ifilter' in kwargs: self.config['IFILTER'] = kwargs['usbh-ifilter']
        if 'usbh-mfilter' in kwargs: self.config['MFILTER'] = kwargs['usbh-mfilter']
        if 'usbh-avg' in kwargs: self.config['AVG'] = kwargs['usbh-avg']
        if 'set_emissivity' in kwargs: self.config['set_emissivity'] = kwargs['set_emissivity']
        

        if params is not {}: self.scan()
        return

    ########################################################################################################################
    # Detect if device is present
    def scan(self,override_params=None):
        self.port = None
        if override_params is not None: self.params = override_params
        
        # Find the tty associated with the serial port
        if 'tty' in self.params.keys():
            self.port = self.params['tty']
        elif 'port' in self.params.keys():
            self.port = self.params['port']
        elif 'pid' in self.params.keys() and 'vid' in self.params.keys(): # USB serial
            
            # This will find all serial ports available to pySerial.
            # We hope the USB device scanned in usbDevice.py can be found here.
            # We need to find an exact match - there may be multiple generic devices.
            from serial.tools import list_ports
            
            # This subroutine will check for matching bus-address locations
            # to identify a particular device even if VID and PID are generic.
            def locationMatch(serialport):
                # Check for bus and port match (for multiple generic serial adapters...)
                if ('port_numbers' in self.params) and ('bus' in self.params) and ('location' in dir(serialport)):
                    search_location = '%i-%s' % (self.params['bus'],'.'.join(['%i'% nn for nn in self.params['port_numbers']]))
                    if search_location == serialport.location:
                        if not self.quiet: print '\tVID:PID match- location %s == %s' % (search_location,\
                                                serialport.location)
                        return True
                    else:
                        if not self.quiet: print '\tVID:PID match but location %s does not match %s' % (search_location,\
                                                serialport.location)
                        return False
                else:
                    # If the feature is unsupported, assume first device is the real one! We can't check.
                    return True
                    
            
            #####################################################################################################################
            # scan all serial ports the OS can see
            for serialport in list_ports.comports():
                
                # Not all versions of pyserial have the list_ports_common module!		
                if 'list_ports_common' in dir(serial.tools):
                    objtype=serial.tools.list_ports_common.ListPortInfo
                else:
                    objtype=None

                # if serialport returns a ListPortInfo object
                if objtype is not None and isinstance(serialport,objtype):
                    
                    thevid = serialport.vid
                    thepid = serialport.pid
                    if thevid==self.params['vid'] and thepid==self.params['pid'] and locationMatch(serialport):
                        self.params['tty']=serialport.device
                        self.port=serialport.device
            
                # if the returned device is a list, tuple or dictionary
                elif len(serialport)>1:

		            # Some versions return a dictionary, some return a tuple with the VID:PID in the last string.
                    if 'VID:PID' in serialport[-1]: # tuple or list
                        thename = serialport[0]
                        # Sometimes serialport[-1] will contain "USB VID:PID=0x0000:0x0000" and
                        # sometimes extra data will follow after, i.e. "USB VID:PID=1234:5678 SERIAL=90ab".
                        if not self.quiet: print '\t',serialport[-1] # report to terminal, useful for debugging.
                        vididx = serialport[-1].upper().index('PID')
                        if vididx <= 0: raise IndexError("Can't interpret USB VID:PID information!")
                        vidpid = serialport[-1][vididx+4:vididx+13] # take fixed set of chars after 'PID='
                        thevid,thepid = [ int(val,16) for val in vidpid.split(':')]
                        if thevid==self.params['vid'] and thepid==self.params['pid'] and locationMatch(serialport):
                            
                            if not self.quiet: print '\t',serialport
                            if thename is not None:
                                self.port = thename # Linux
                            else:
                                self.port = serialport.device # MacOS
                            if not self.tty_prefix in self.port: self.port = self.tty_prefix + self.port
                            self.params['tty']=self.port

                    elif 'vid' in dir(serialport): # dictionary
                        if serialport.vid==self.params['vid'] and serialport.pid==self.params['pid'] and locationMatch(serialport):
                            # Vid/Pid matching
                            if not self.quiet: print '\t',serialport.hwid, serialport.name
                            if serialport.name is not None:
                                self.port = serialport.name # Linux
                            else:
                                self.port = serialport.device # MacOS
                            if not self.tty_prefix in self.port: self.port = self.tty_prefix + self.port
                            self.params['tty']=self.port

                # List or dict with only one entry.
                elif len(list_ports.comports())==1: # only one found, use as default
                    self.port = serialport[0]
                    if not self.tty_prefix in self.port: self.port = self.tty_prefix + self.port
                    self.params['tty']=self.port

                if 'tty' in self.params:
                    if os.path.exists(self.params['tty']): break
            #####################################################################################################################
        
        if self.port is None:
            print "\tUnable to connect to serial port - port unknown."
            print "\tYou may need to install a specific USB-to-Serial driver."
            print "\tfound non-matching ports:",list_ports.comports()[0]
            raise pyLabDataLoggerIOError("Serial port driver missing")
        
        else: self.activate()
        return

    ########################################################################################################################
    # Establish connection to device (ie open serial port)
    def activate(self):
    
        # Over-ride serial comms parameters for special devices
        if self.subdriver=='omega-iseries':
            if not 'bytesize' in self.params.keys(): self.params['bytesize']=serial.SEVENBITS
            if not 'parity' in self.params.keys(): self.params['parity']=serial.PARITY_ODD
            if not 'stopbits' in self.params.keys(): self.params['stopbits']=serial.STOPBITS_ONE
            if not 'baudrate' in self.params.keys(): self.params['baudrate']=2400
            self.params['timeout']=1
        elif self.subdriver=='tds220gpib':
            if not 'baudrate' in self.params.keys(): self.params['baudrate']=460800
            if not 'gpib-address' in self.params.keys(): self.params['gpib-address']=1 # default GPIB address is 1
        elif self.subdriver=='sd700':
            if not 'xonxoff' in  self.params.keys(): self.params['xonxoff']=True
            if not 'timeout' in self.params.keys(): self.params['timeout']=5
        elif self.subdriver=='alicat':
            if not 'baudrate' in self.params.keys(): self.params['baudrate']=19200
            if not 'ID' in self.params.keys(): self.params['ID']='A' # default unit ID is 'A'
        elif self.subdriver=='omega-usbh':
            if not 'baudrate' in self.params.keys(): self.params['baudrate']=115200
        
        # Default serial port parameters passed to pySerial
        if not 'baudrate' in self.params.keys(): self.params['baudrate']=9600
        if not 'bytesize' in self.params.keys(): self.params['bytesize']=serial.EIGHTBITS
        if not 'parity' in self.params.keys(): self.params['parity']=serial.PARITY_NONE
        if not 'stopbits' in self.params.keys(): self.params['stopbits']=serial.STOPBITS_ONE
        if not 'xonxoff' in  self.params.keys(): self.params['xonxoff']=False
        if not 'rtscts' in  self.params.keys(): self.params['rtscts']=False
        if not 'timeout' in self.params.keys(): self.params['timeout']=1. # sec for a single byte read/write
        
        # Default serial comms parameters used in this class
        if not 'timeout_total' in self.params.keys(): self.params['timeout_total']=10. # sec for total request loop
        if not 'min_response_length' in self.params.keys(): self.params['min_response_length']=0 # bytes
        
        if not self.quiet: print "\tOpening serial port %s: %s (%i, %s, %s, %s, %s, %i)" % (self.port,\
                                    self.params['baudrate'],\
                                    self.params['bytesize'], self.params['parity'],\
                                    self.params['stopbits'], self.params['xonxoff'],\
                                    self.params['rtscts'], self.params['timeout'])
                                    
        self.Serial = serial.Serial(port=self.port, baudrate=self.params['baudrate'],\
                                    bytesize=self.params['bytesize'], parity=self.params['parity'],\
                                    stopbits=self.params['stopbits'], xonxoff=self.params['xonxoff'],\
                                    rtscts=self.params['rtscts'], timeout=self.params['timeout'])
        
        self.driverConnected=True
                                    
        # Make first query to get units, description, etc.
        self.query(reset=True)
        if not self.quiet: self.pprint()
        return

    ########################################################################################################################
    # Deactivate connection to device (close serial port)
    def deactivate(self):
        self.Serial.close()
        self.driverConnected=False
        return

    ########################################################################################################################
    # Apply configuration changes to the driver (subdriver-specific)
    def apply_config(self):
        subdriver=self.subdriver
        try:
            assert(self.Serial)
            if self.Serial is None: raise pyLabDataLoggerIOError("Could not access serial port.")

            # Apply subdriver-specific variable writes
            if subdriver=='tds220gpib':
                # No settings can be modified at present.
                # In future we could change voltage or time scale or switch channels on/off.
                pass
            elif subdriver=='omega-ir-usb':
                e=self.config['set_emissivity']
                if (e is not None) and (e>0) and (e<=1.): self.Serial.write("E%0.2f\n" % float(e))
                else: raise ValueError
            elif subdriver=='omega-usbh':
                for var in ['IFILTER','MFILTER','AVG','RATE']:
                    if self.config[var] != self.blockingSerialRequest(var+'\r\n','\r').split('=')[-1]:
                        self.config[var] = self.blockingSerialRequest('%s %s\r\n' % (var,self.config[var]),'\r',min_response_length=8).split('=')[-1]
                # Write human readable sample rate
                if int(self.config['RATE'])==0:   self.config['sample_rate_Hz'] = 5
                elif int(self.config['RATE'])==1: self.config['sample_rate_Hz'] = 10
                elif int(self.config['RATE'])==2: self.config['sample_rate_Hz'] = 20
                elif int(self.config['RATE'])==3: self.config['sample_rate_Hz'] = 40
                elif int(self.config['RATE'])==4: self.config['sample_rate_Hz'] = 80
                elif int(self.config['RATE'])==5: self.config['sample_rate_Hz'] = 160
                elif int(self.config['RATE'])==6: self.config['sample_rate_Hz'] = 320
                elif int(self.config['RATE'])==7: self.config['sample_rate_Hz'] = 640
                elif int(self.config['RATE'])==8: self.config['sample_rate_Hz'] = 1000
                else: raise ValueError("omega-usbh: unknown RATE value %s [valid options are integers 0-8]" % self.config['RATE'])   
                # update maxlen
                if not 'sample_period' in self.params: self.params['sample_period']=1.
                # 6-10 bytes per sample, * sample period, * samples per second, dictates maxlen returned for 'PC'
                self.maxlen= int(6*(self.params['sample_period']*self.config['sample_rate_Hz']+1))

            elif subdriver=='ohaus7k':
                # No settings can be modified at present. In future we could allow tare/zero or
                # a change of units.
                pass
            elif subdriver=='center310':
                # No settings can be modified at present.
                # The comms is one-way, the device cannot be controlled remotely.
                pass
            elif subdriver=='omega-iseries':
                # No settings can be modified at present. In future we could allow changing of
                # set points.
                pass
            elif subdriver=='sd700':
                # No settings can be modified.
                pass
            elif subdriver=='alicat':
                # No settings can be modified at present. In future we could set units and gas type
                # from software.
                pass
            elif subdriver=='tc08rs232':
                raise RuntimeError("Need to implement selection of thermocouple types! Contact the developer.")
            else:
                print self.__doc__
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])
    
        except ValueError:
            raise
        
        return

    ########################################################################################################################
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

    ########################################################################################################################
    # Blocking call to send a request and get a string back.
    # This method block is for devices that use a standard
    # method; call<CR/LF> -short delay- response<CR/LF>.
    # Works well for most RS-232 devices.
    def blockingSerialRequest(self,request,terminationChar='\r',maxlen=1024,min_response_length=0,sleeptime=0.01):
        try:
            s=''
            response=None
            if len(request)>0:
                if not self.quiet:
                    sys.stdout.write('\t'+self.port+':'+repr(request)+'\t')
                    sys.stdout.flush()
                self.Serial.write(request)
            t_=time.time()
            time.sleep(sleeptime)
            while len(s)<maxlen:
                s+=self.Serial.read(1)
                if len(s) == 0: # response timed out
                    break
                if (s[-1] == terminationChar) and (len(s)>min_response_length):
                    response=s.strip()
                    break
                if (time.time() - t_) > self.params['timeout_total']: raise pyLabDataLoggerIOError("timeout")
            if not self.quiet: sys.stdout.write(repr(response)+'\n')
        except pyLabDataLoggerIOError:
            pass
        return response
    
    ########################################################################################################################
    # Special function to handle reading data that shouldn't have any special characters stripped out.
    # This is useful if the length of the data could be arbitrary and not even whole numbers of bytes,
    # or if the read command doesn't reliably returned buffered data (i.e. for RS-485 where there is
    # some delay for the direction switching)
    def blockingRawSerialRequest(self,request,terminationChar='\r',maxlen=1024,min_response_length=0,sleeptime=0.01):
        try:
            #print repr(request) # debugging
            if len(request)>0: self.Serial.write(request)
            t_=time.time()
            time.sleep(sleeptime)
            data=''
            while len(data)<maxlen:
                data += self.Serial.read(1)
                if len(data) > 0:
                    if (data[-1] == terminationChar) and (len(data)>min_response_length):
                        break
                if (time.time() - t_) > self.params['timeout_total']: raise pyLabDataLoggerIOError("timeout")
        except pyLabDataLoggerIOError:
            pass
        return data
    
    ########################################################################################################################
    # Configure device based on what sub-driver is being used.
    # This is done when self.query(reset=True) is called, as at
    # this point we might need to poll the device to check a setting.
    def configure_device(self):
    
        subdriver = self.subdriver
        
        # By default, using blockingSerialRequest and 1024 maxlen, 10ms wait between request & reply
        self.serialCommsFunction = self.blockingSerialRequest
        self.maxlen = 1024
        self.sleeptime = 0.01

        # ----------------------------------------------------------------------------------------
        if subdriver=='tds220gpib': # Startup config for Tektronix TDS220 series via GPIB to serial
            # Configure USB-GPIB adapter to talk to bus device no. 1
            self.blockingSerialRequest('++addr %i\r' % self.params['gpib-address'],terminationChar='\r',min_response_length=0)
            # Configure USB-GPIB to automatically send data back when we make a query
            self.blockingSerialRequest('++auto 1\r',terminationChar='\r',min_response_length=0)
            
            # Find out what model we have
            idstring = self.blockingSerialRequest('ID?\r\n',terminationChar='\r',min_response_length=1)
            if idstring is None:  raise pyLabDataLoggerIOError("no response from oscilloscope") 
            else: print "\tGPIB Address %i: Device ID string = %s" % (self.params['gpib-address'],idstring)
            
            if 'TDS 220' in idstring: 
                self.name = "Tektronix TDS220"
                self.params['n_channels']=2
            elif 'TDS 210' in idstring:
                self.name = "Tektronix TDS210"
                self.params['n_channels']=2
            elif 'TDS 224' in idstring:
                self.name = "Tektronix TDS224"
                self.params['n_channels']=4
            else:
                raise pyLabDataLoggerIOError("Unknown model %s" % idstring)
            
            # Set up device
            self.params['id']=idstring
            self.config['channel_names']=['Time']
            self.config['channel_names'].extend(['CH%i' % n for n in range(self.params['n_channels'])])
            self.params['raw_units']=['']
            self.params['raw_units'].extend(['']*self.params['n_channels'])
            sself.config['eng_units']=['']
            self.config['eng_units'].extend(['']*self.params['n_channels'])
            self.config['scale']=[1.]*self.params['n_channels']
            self.config['offset']=[0.]*self.params['n_channels']
            self.serialQuery=None
            self.serialQuery.extend([':DAT:SOU CH%i,WAVF?' % n for n in range(self.params['n_channels'])]) # To set!
            self.queryTerminator='\r\n'
            self.responseTerminator='\r'
            self.maxlen=999999 # large chunks of data will come back!
            self.sleeptime=0.5

        # ----------------------------------------------------------------------------------------
        elif subdriver=='omega-ir-usb': # Statup config for IR-USB
            self.name = "Omega IR-USB"
            self.config['channel_names']=['tempC','tempF','ambientC','ambientF','emissivity']
            self.params['raw_units']=['C','F','C','F','']
            self.config['eng_units']=['C','F','C','F','']
            self.config['scale']=[1.,1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.,0.]
            self.params['n_channels']=5
            self.serialQuery=['C','F','A','E']
            self.queryTerminator='\r\n'
            self.responseTerminator='\r'
            self.config['set_emissivity']=None

        # ----------------------------------------------------------------------------------------
        elif subdriver=='omega-usbh':
            self.name = "Omega USB High-Speed Pressure Transducer"
            self.config['channel_names']=['pressure']
            self.params['raw_units']=['psia']
            self.config['eng_units']=['psia']
            self.config['scale']=[1.]
            self.config['offset']=[0.]
            self.params['n_channels']=1
            self.serialQuery=['PC,,PS']
            self.queryTerminator='\r\n'
            self.responseTerminator=''
            self.serialCommsFunction=self.blockingRawSerialRequest
            # First ensure that streaming is inactive.
            self.Serial.write('PS')
            self.blockingSerialRequest('SNR\r\n','\r') # dummy command to flush buffer
            # Get unit ID and serial
            self.params['Info'] = self.blockingSerialRequest('ENQ\r\n','\r',min_response_length=36).replace('\r\n',' ')
            self.params['ID'] = self.blockingSerialRequest('SNR\r\n','\r').split('=')[-1]
            if self.params['ID'].strip() != '': self.name += ' '+self.params['ID'].strip()
            # Get filter settings and sample rate
            for var in ['IFILTER','MFILTER','AVG','RATE']:
                if not var in self.config:
                    self.config[var] = self.blockingSerialRequest(var+'\r\n','\r').split('=')[-1]
            # Apply user-set filter and sample rate setting to the client device
            self.apply_config()
            # Write human readable sample rate
            if int(self.config['RATE'])==0:   self.config['sample_rate_Hz'] = 5
            elif int(self.config['RATE'])==1: self.config['sample_rate_Hz'] = 10
            elif int(self.config['RATE'])==2: self.config['sample_rate_Hz'] = 20
            elif int(self.config['RATE'])==3: self.config['sample_rate_Hz'] = 40
            elif int(self.config['RATE'])==4: self.config['sample_rate_Hz'] = 80
            elif int(self.config['RATE'])==5: self.config['sample_rate_Hz'] = 160
            elif int(self.config['RATE'])==6: self.config['sample_rate_Hz'] = 320
            elif int(self.config['RATE'])==7: self.config['sample_rate_Hz'] = 640
            elif int(self.config['RATE'])==8: self.config['sample_rate_Hz'] = 1000
            else: raise ValueError("omega-usbh: unknown RATE value %s" % self.config['RATE'])
            print "\tomega-usbh: Sample rate %i Hz" % self.config['sample_rate_Hz']
            # Get/set sampling period. Default 1 second.
            if not 'sample_period' in self.params: self.params['sample_period']=1.
            # 6-10 bytes per sample, * sample period, * samples per second, dictates maxlen returned for 'PC'
            self.maxlen= int(6*(self.params['sample_period']*self.config['sample_rate_Hz']+1))

        # ----------------------------------------------------------------------------------------
        elif subdriver=='ohaus7k': # Startup config for OHAUS Valor 7000
            #Get the units currently set on the display
            unit='?'
            unit=self.blockingSerialRequest('PU\r\n','\r')
            if unit is None: unit='?'
            elif unit == 'N': unit = 'Net' # not Newtons!
            # Fixed settings.
            self.name = "OHAUS Valor 7000 Scale"
            self.config['channel_names']=['weight']
            self.params['raw_units']=[unit]
            self.config['eng_units']=[unit]
            self.config['scale']=[1.]
            self.config['offset']=[0.]
            self.params['n_channels']=1
            self.serialQuery=['IP']
            self.queryTerminator='\r\n'
            self.responseTerminator='\r'

        # ----------------------------------------------------------------------------------------
        elif subdriver=='wtb': # Startup config for Radwag WTB scale
            # Fixed settings.
            self.name = "Radwag WTB series balance"
            self.config['channel_names']=['weight']
            self.params['raw_units']=['?']
            self.config['eng_units']=['?']
            self.config['scale']=[1.]
            self.config['offset']=[0.]
            self.params['n_channels']=1
            self.serialQuery=['SUI']
            self.queryTerminator='\r\n'
            self.responseTerminator='\r'


        # ----------------------------------------------------------------------------------------
        elif subdriver=='center310': # Startup config for CENTER 310
            self.name = "Center 310 Humidity/Temperature meter"
            self.config['channel_names']=['humidity','temperature','timer','hold','min_max']
            self.params['raw_units']=['%','','s','',''] # temp units will be determined when query runs
            self.config['eng_units']=['%','','s','','']
            self.config['scale']=[1.,1.,1.,1.,1.]
            self.config['offset']=[0.,0.,0.,0.,0.]
            self.params['n_channels']=5
            self.serialQuery=['A'] # This will return everything except the model number
            self.queryTerminator='\r\n'
            self.responseTerminator='\x03' # The "K" query terminates in \r\n but the "A" terminates in 0x03
            self.params['min_response_length']=4 # bytes
            
            # Confirm model number. Send 'K' and response will be \r\n terminated.
            self.params['ID']=self.blockingSerialRequest('K\r\n','\r')
            print "\tReturned Model ID =",self.params['ID']

            
        # ----------------------------------------------------------------------------------------
        elif subdriver=='omega-iseries': # Startup config for Omega iSeries Process Controller
            self.name = "Omega iSeries Process Controller"
            if not 'units' in self.params: u='degC'
            else: u=self.params['units']
            self.config['channel_names']=['Current Value','Set Point 1','Set Point 2','Alarm']
            self.params['n_channels']=len(self.config['channel_names'])
            self.params['raw_units']=[u,u,u,'']
            self.config['eng_units']=[u,u,u,'']
            self.config['scale']=[1.]*self.params['n_channels']
            self.config['offset']=[0.]*self.params['n_channels']
            if '485' in self.driver:
                if not self.quiet: print '\tRS-485 comms mode with fixed address = 01'
                #RS-485 requires commands to be prepended with the device's address
                self.serialQuery=['*\xb01X\xb01',\
                                  '*\xb01R\xb01',\
                                  '*\xb01R\xb02',\
                                  '*\xb01U\xb01']
            else: # RS-232
                if not self.quiet: print '\tRS-232 comms mode with fixed address = 01'
                self.serialQuery=['*\xb01X\xb01',\
                                  '*\xb01R\xb01',\
                                  '*\xb01R\xb02',\
                                  '*\xb01U\xb01']
            self.queryTerminator='\r'
            self.responseTerminator='\r'
            self.serialCommsFunction=self.blockingRawSerialRequest
            self.params['min_response_length']=1 # bytes

            # Try and establish communication with the device. !!!
            self.params['version']=None
            time.sleep(1.)  #settling time
            while True:
                req='*\xb01R\xb05\r'
                print "Send",repr(req)
                ver=self.blockingRawSerialRequest(req,terminationChar='',\
                                 sleeptime=.01,min_response_length=1,maxlen=64)
                #ver=struct.unpack('>3c',ver)
                print "Read",repr(ver)
                #self.params['version'] = repr(ver)#ver[0]+binascii.hexlify(ver[1])
                #if self.params['version'][0] == 'V': break
                time.sleep(.1)
            print '\tISeries ID =',self.params['version']


        # ----------------------------------------------------------------------------------------
        elif subdriver=='tc08rs232': # Startup config for TC-08 over RS-232
            self.name = "Picolog RS-232 TC-08 thermocouple datalogger"
            self.config['channel_names']=['T1','T2','T3','T4','T5','T6','T7','T8','Cold Junction Reference','Cold Junction Thermistor']
            if 'init_tc08_config' in self.params: self.config['tc_config'] = self.params['init_tc08_config']
            else: self.config['tc_config'] = ['K','K','K','K','K','K','K','K','','']
            self.params['n_channels']=10
            self.params['raw_units']=['C','C','C','C','C','C','C','C','','']
            self.config['eng_units']=['C','C','C','C','C','C','C','C','','']
            self.config['scale']=[1.]*self.params['n_channels']
            self.config['offset']=[0.]*self.params['n_channels']
            self.serialQuery = [ struct.pack('>B',n) for n in [ 0,20,40,60,80,0xA0,0xC0,0xE0,0x22,0x42 ] ]
            self.queryTerminator=''
            self.responseTerminator=''
            self.serialCommsFunction=self.blockingRawSerialRequest
            self.params['min_response_length']=3 # bytes
            self.maxlen=3

            # Set RTS and DTR to provide power to the device, as per user manual.
            # Have confirmed these are the right ones.
            self.Serial.rts = True
            self.Serial.dtr = False
            time.sleep(1.)

            # Try and get device version code.
            self.params['version']=None
            time.sleep(1.)  #settling time
            while True:
                ver=struct.unpack('>3c',self.blockingRawSerialRequest(struct.pack('>B',1),terminationChar='',\
                                                              sleeptime=.01,min_response_length=3,maxlen=3))
                self.params['version'] = ver[0]+binascii.hexlify(ver[1])
                if self.params['version'][0] == 'V': break
                time.sleep(.5)
            print '\tTC08 version =',self.params['version']
            
        # ----------------------------------------------------------------------------------------
        elif subdriver=='sd700':
            # 9600 8N1 XonXoff active
            # Mode 2 switch selected
            self.name = "Extech SD700 Barometric PTH Datalogger"
            self.config['channel_names']=['humidity','temperature','pressure']
            self.params['raw_units']=['%','degC','hPa'] # temp units will be determined when query runs
            self.config['eng_units']=['%','degC','hPa']
            self.config['scale']=[1.,1.,1.]
            self.config['offset']=[0.,0.,0.]
            self.params['n_channels']=3
            self.serialQuery=['','',''] # The device streams data regardless of TX signal.
            self.queryTerminator=''
            self.responseTerminator='\r'
            self.params['min_response_length']=8 # bytes


        # ----------------------------------------------------------------------------------------
        elif subdriver=='alicat':
            self.name = "Alicat Scientific M-series mass flow meter" # update w/model number later
            self.params['n_channels']=5
            self.config['channel_names']=['','','','',''] # will be obtained by query below
            self.params['raw_units']=['','','','',''] # will be obtained by query below
            self.config['eng_units']=['','','','',''] # will be obtained by query below
            self.config['scale']=[1.,1.,1.,1.,np.nan]
            self.config['offset']=[0.,0.,0.,0.,np.nan]
            if not 'ID' in self.params.keys(): self.params['ID']='A' # default unit ID is 'A'
            self.serialQuery=[self.params['ID']] # one command returns all the variables.
            self.queryTerminator='\r'
            self.responseTerminator='\r'
            self.params['min_response_length']=1 # bytes

            # talk to flowmeter-
            # get params for model, serial number etc, and add to device name for uniqueness in logfile
            self.params['model']=self.blockingSerialRequest(self.params['ID']+'??m4'+self.queryTerminator,'\r')
            self.params['serial']=self.blockingSerialRequest(self.params['ID']+'??m5'+self.queryTerminator,'\r')
            self.params['cal_date']=self.blockingSerialRequest(self.params['ID']+'??m7'+self.queryTerminator,'\r')
            self.params['firmware']=self.blockingSerialRequest(self.params['ID']+'??m9'+self.queryTerminator,'\r')
            try:
                serialNumInt = int(self.params['serial'].split(' ')[-1])
                modelString  = self.params['model'].split(' ')[-1]
                self.name += ' %s %i' % (modelString,serialNumInt)
            except:
                # in case serial num etc invalid or empty
                pass

            # get units & channel names
            for j in range(2,7):
                descStr = self.blockingSerialRequest(self.params['ID']+'??d%i' % j +self.queryTerminator,'\r')
                try:
                    unitStr = descStr.split(' ')[-1].replace('`','deg')
                    nameStr = ' '.join(descStr.split(' ')[3:6]).strip()
                    if j<6: # skip units for 'gas type'
                        self.params['raw_units'][j-2] = unitStr
                        self.config['eng_units'][j-2] = unitStr
                    self.config['channel_names'][j-2]=nameStr
                except:
                    raise pyLabDataLoggerIOError("Unable to parse Alicat channel descriptor string.\nCheck the baud rate is %i and the device ID is %s" % (self.params['baudrate'],self.params['ID']))
            
        else:
            raise KeyError("I don't know what to do with a device driver %s" % self.params['driver'])
        return

    ########################################################################################################################
    # Convert string responses from serial port into usable numbers/values
    def convert_raw_string_to_values(self, rawData, requests=None):
        self.lastValue=[np.nan]*self.params['n_channels']
        # Parse depending on subdriver
        subdriver = self.subdriver
        try:
            # Catch all types of failed serial reads.
            if len(rawData)==0: raise IndexError
            elif rawData is None: raise IndexError
            elif rawData[0] is None: raise IndexError
            elif len(rawData[0]) is None: raise IndexError

            # ----------------------------------------------------------------------------------------
            if subdriver=='tds220gpib':
            
                processed_curves = []
                self.params['info'] = ['']
                for i in range(1,len(rawData)):
                    l=rawData[i].split(';') # Break apart header & data.
                    def tryfloat(val):
                        try: return float(val)
                        except ValueError: return val
                    # Get all the header variables.
                    byt_nr, bit_nr, encoding, bn_fmt, byt_or, nr_pt, wfid, pt_fmt, xincr, pt_off, xzero,\
                        xunit, ymult, yzero, yoff, yunit = [tryfloat(v.strip()) for v in l[:16]]
                    
                    if encoding == 'BIN': # Binary decode with struct.unpack
                        if byt_or == 'LSB': decode_string = '<'
                        else: decode_string = '>'
                        x_ = int(l[16][1])
                        buf_len = int(l[16][2:2+x_])
                        decode_string += 'x'*(2+x_)
                        decode_string += str(int(buf_len))
                        if bn_fmt == 'RP': # Signed or unsigned binary?
                            if byt_nr == 1: decode_string += 'B'
                            elif byt_nr == 2: decode_string += 'H'
                            elif byt_nr == 4: decode_string += 'I'
                            elif byt_nr == 8: decode_string += 'Q'
                            else: raise ValueError("TDS22x decoder: Unknown bytes per sample %s" % byt_nr)
                        elif bn_fmt == 'RI':
                            if byt_nr == 1: decode_string += 'b'
                            elif byt_nr == 2: decode_string += 'h'
                            elif byt_nr == 4: decode_string += 'i'
                            elif byt_nr == 8: decode_string += 'q'
                            else: raise ValueError("TDS22x decoder: Unknown bytes per sample %s" % byt_nr)
                        else:
                            raise ValueError("TDS22x decoder: Unknown binary format")
                        
                        buf = struct.unpack(decode_string, l[16])
                    
                    elif encoding == 'ASC': # Ascii decode. Always a signed integer.
                        x_ = int(l[16][1])
                        buf_len = int(l[16][2:2+x_])
                        buf = [int(v) for v in l[16][2+x_:]]
                
                    if i==1: # Add time axis
                        processed_curves.append(np.linspace(xzero, xzero+xincr*nr_pt, nr_pt))
                        self.params['raw_units'][0]=xunit
                        if self.config['eng_units'][0] == '': self.config['eng_units'][0] = xunit
                        
                    # Add voltage trace
                    processed_curves.append((np.array(buf).astype(np.float) - yoff)*ymult)
                    
                    # Add units & scaling factors.
                    self.config['raw_units'][i]=yunit
                    if self.config['eng_units'][i] == '': self.config['eng_units'][i] = yunit
    
                    # Add wfid string to params
                    self.params['info'].append(wfid)
    
                return processed_curves

            # ----------------------------------------------------------------------------------------
            elif subdriver=='tc08rs232':
                # This algorithm follows the TC-08 user manual.
                # Each call returns 3 bytes, the first is the sign and the second two are the MSB and LSB
                microvolts = np.array([ struct.unpack('>H',s[1:]) for s in rawData ]).astype(np.float)
                # Apply sign
                for n in range(len(microvolts)):
                    neg = struct.unpack('?',rawData[n][0])
                    if neg: microvolts[n] *= -1
                microvolts *= 0.9082780194 # 65535 counts == 59524uV
                # Calculate cold junction temperature
                divisor = (microvolts[9] + 65535)/65536.
                r = (65536 * (microvolts[9]/divisor)) / (microvolts[8]/divisor)
                cold_junction = -3.63620e-25*r**5 + 2.81708e-19*r**4 - 8.70805e-14*r**3 + 1.39391e-8*r**2 - 1.31981e-3*r + 71.3437
                # Convert to temperature
                temp = np.zeros_like(microvolts)
                from thermocouples_reference import thermocouples
                for n in range(8):
                    tc=thermocouples[self.config['tc_config'][n].upper()]
                    if self.params['raw_units'][n] == 'C': fconversion = tc.inverse_CmV
                    elif self.params['raw_units'][n] == 'F': fconversion = tc.inverse_FmV
                    elif self.params['raw_units'][n] == 'R': conversion = tc.inverse_RmV
                    elif self.params['raw_units'][n] == 'K': fconversion = tc.inverse_KmV
                    else: raise KeyError("Unknown units of measurement")
                    temp[n] = fconversion(microvolts[n]/1000., Tref=cold_junction)
                temp[-1] = cold_junction
                return temp

            # ----------------------------------------------------------------------------------------
            elif subdriver=='omega-ir-usb':
                if len(rawData)<2: return [None]*self.params['n_channels']
                vals= [float(rawData[0].strip('>')), float(rawData[1].strip('>'))]
                if len(rawData)<3: vals.extend([np.nan, np.nan])
                else: vals.extend([float(v) for v in rawData[2].split('=')[1].split(',')])
                if len(rawData)<4: vals.append(np.nan)
                else: vals.append(float(rawData[3].split('=')[1]))
                return vals

            # ----------------------------------------------------------------------------------------
            elif subdriver=='omega-usbh':
                vals = []
                for i in range(len(rawData)):
                    
                    # first frame beginning point
                    offset = rawData[i].index('\xaa')
                    # Remove 0xAAAA and replace with 0xAA (delete the bit stuff)
                    rawData[i] = rawData[i].replace('\xaa\xaa','\xaa')
                    # number of frames to process
                    n_frames = int(np.floor(len(rawData[i][offset:])/6))                   
                    vals.append( np.array( struct.unpack('<'+'xxf'*n_frames,rawData[i][offset:offset+n_frames*6]) ) )
                    
                return vals

            # ----------------------------------------------------------------------------------------
            elif subdriver=='ohaus7k':
                vals=rawData[0].split(' ')
                self.params['raw_units']=[vals[-1].strip()]
                return [float(vals[0])]

            # ----------------------------------------------------------------------------------------
            elif subdriver=='wtb':
                vals=rawData[0].strip().split(' ')
                self.params['raw_units']=[vals[-1]]
                if self.config['eng_units'][0] == '?': self.config['eng_units']=[vals[-1]]
                return [float(vals[-2])]

            # ----------------------------------------------------------------------------------------
            elif subdriver=='center310':
                '''
                    Software transmits 0x41 / A to request a normal report. or 0x4b / K for the model number.
                    The meter responds with 0x02 ModeChar and then a sequence of strings containing
                    hex data in ASCII format seperated by \n each.
                    There are 4 to 9 bytes returned depending on the meter's operating mode.                    
                    ModeChar represents the mode of the meter, as follows:
                    Mode 'P' is a normal report of humidity, temperature in C, and time in free run mode.
                    Mode 'H' is normal free run in Farenheit.
                    Mode 'Q' is MAX
                    Mode 'R' is MIN
                    Mode 'S' is MAX MIN
                    Mode 'T' is HOLD
                    Mode '\x10' happens after some period of continuous running, and I'm not sure what this means exactly. 
                    It might be related to the auto-off feature or when the auto-off is disabled. Otherwise the device behaves as in 'P' mode.
                '''
                #print '\t0x'+rawData[0].encode('hex') # Debugging
                hold=0; minmax=0; prefix_data=''
                while (rawData[0][0] != '\x02') and (rawData[0][1] < '\x41'):
                    # Advance forwards in the string until we find 0x02 followed by an ASCII capital letter.
                    # Put everything before this into 'prefix_data' for later processing.
                    prefix_data += rawData[0][0]
                    rawData[0] = rawData[0][1:]
                # Get the mode string
                mode = rawData[0][1].strip()
                # Determine the units, hold and minmax values from the mode string
                if 'P' in mode: self.params['raw_units'][1]='C'
                elif 'T' in mode: hold=1
                elif 'R' in mode: minmax=1
                elif 'Q' in mode: minmax=2
                elif 'S' in mode: minmax=3
                elif 'H' in mode: self.params['raw_units'][1]='F'
                elif '\x10' in mode: pass
                else: 
                    print "\t!! Unknown device mode string in serial response"
                    raise ValueError
                if len(rawData[0])<6: raise ValueError # Short/corrupted responses.
                decoded=rawData[0][2:] # Everything after the mode string is T&H data
                humidity = np.nan; temperature = np.nan # Default to NaN
                time_min = np.nan; time_sec = np.nan
                flags = None
                
                if mode is 'H': # Farenheit mode puts the timer data before the mode string
                    humidity = np.array(struct.unpack('>H', decoded[1:3]))[0]/10.
                    temperature = np.array(struct.unpack('>H', decoded[3:]+'\x00'))[0]/10.
                    if len(prefix_data) > 2:
                        time_min, time_sec = np.array(struct.unpack('>bb', prefix_data[-3:-1]))
                else: # Celsius mode
                    if len(decoded)>4:
                        humidity, temperature = np.array(struct.unpack('>2H', decoded[1:5]))/10.
                    if len(decoded)>=7:
                        time_min, time_sec = np.array(struct.unpack('>bb', decoded[5:7]))
                    if len(decoded)>=8:
                        flags = decoded[7:] # Flag tells us if a mode change is going to happen
                self.params['mode']=mode.strip()
                if flags is None: self.params['flags']=''
                else: self.params['flags']=flags.strip()
                return [humidity, temperature, time_min*60 + time_sec, hold, minmax]

            # ----------------------------------------------------------------------------------------
            if subdriver=='omega-iseries':
                """ Omega iSeries returns binary that doesn't always conform to ASCII standard.
                    The number of bits returned can also vary. Values from RAM are converted to
                    quasi-ascii format while values in EEPROM tend to be in a custom binary floating
                    point format."""
                vals=[]
                for n in range(len(rawData)):
                    data = rawData[n]
                    request = requests[n]
                    
                    
                    if 'R' in request:
                        # 'R' indicates reading a set point from flash memory, this must be decoded from binary.
                        #print repr(request), repr(data.strip()[5:])
                        decoded = data.strip()[6:].replace('\xae','\x2e').replace('\xb0','0').replace(r'\xb','')
                        
                        value = float(int(decoded[3:],16))
                        #print "{0:x}".format(int(decoded[:3],16))
                        decimal_bits = (int(decoded[:3],16) >> 8) & 0x7
                        if decimal_bits == 0x2: value /= 10.
                        if decimal_bits == 0x3: value /= 100.
                        if decimal_bits == 0x4: value /= 1000.
                        sign_bit = int(decoded[:3],16) >> 11
                        if sign_bit == 0x1: value = -value
                        #print value
                        vals.append(value)
                        #print value
                    elif 'X' in request or 'U' in request:
                        # 'X' indicates reading a value from RAM already formatted in ASCII.
                        # 'U' is a status code.
                        # Simple float conversion should work.
                        try:
                            if 'X\xb02' in request: start_byte = 6
                            else:
                                start_byte = 5
                                if data[start_byte]=='1': start_byte+=1
                            #print repr(request), repr(data.strip()[start_byte:])
                            decoded = data.strip()[start_byte:].replace('\xae','\x2e').replace('\xb0','0').replace('\xb1','1').replace('\xb2','2')
                            decoded = decoded.replace('\xb3','3').replace('\xb4','4').replace('\xb5','5').replace('\xb6','6').replace('\xb7','7')
                            decoded = decoded.replace('\xb8','8').replace('\xb9','9').replace('\xb0','0')
                            #print repr(decoded), decoded
                            vals.append(float(decoded))
                        except ValueError as e:
                            print e
                            vals.append(np.nan)
                            continue
                    else:
                        
                        raise KeyError("I don't know how to decode this serial command")

                return vals

            # ----------------------------------------------------------------------------------------
            if subdriver=='sd700':
                vals = []
                for i in range(len(rawData)):

                    if len(rawData[i])==15: # \x00\x00 starting
                        strdata = struct.unpack('15c',rawData[i])
                    elif len(rawData[i])==13:
                        strdata = struct.unpack('13c',rawData[i])
                        strdata = ['','']+strdata
                    else:
                        strdata = struct.unpack('%ic' % len(rawData[i]),rawData[i])
                        if len(strdata)>15: strdata = strdata[-15:]
                    vals.append(float(''.join(strdata[-8:]))*0.1)
                    #debugging:
                    #print repr(''.join(strdata[:9])) # this bit probably indicates -ve sign, units, etc.
                return vals

            # ----------------------------------------------------------------------------------------
            if subdriver=='alicat':
                valStrings= [ s for s in rawData[0].split(' ') if s!='' ]
                if valStrings[0].upper() != self.params['ID'].upper(): raise pyLabDataLoggerIOError("Alicat Device ID mismatch - wrong serial port?")
                print self.config['channel_names']
                return [ float(valStrings[1]), float(valStrings[2]), float(valStrings[3]), float(valStrings[4]), valStrings[5].strip() ]

            else:
                raise KeyError("I don't know what to do with a device driver %s" % self.params['driver'])
        except ValueError:
            print "\t!! Failure to unpack raw string from device:", rawData
        except IndexError: # Nothing in rawData!
            print "\tDevice %s returned no data." % self.name
        
        return [np.nan]*self.params['n_channels']
    
    
    
    ########################################################################################################################
    # Read latest values
    def get_values(self):
        rawData=[]
        for n in range(len(self.serialQuery)):
            if ',' in self.serialQuery[n]:
                # Multiple commands must be sent. They are seperated by commas.

                # A double comma denotes a long pause dictated by params['sample_period']
                # The responses will be concatenated.
                if ',,' in self.serialQuery[n] and not 'sample_period' in self.params:
                    self.params['sample_period']=1.
                    print "sample_period not set for %s, default to 1 second" % self.name

                # Split commands,set default values.
                cmds=self.serialQuery[n].split(',')
                resp='' 
                maxlen = self.maxlen
                sleeptime = self.sleeptime
                # Loop commands
                for i in range(len(cmds)):
                    if i<len(cmds)-1: 
                        if cmds[i+1]=='': # ',,' pause will come next
                            sleeptime = self.params['sample_period'] # set the pause period longer

                    if cmds[i]=='': # ',,' was detected
                        maxlen=0 # following command is a 'stop' command and no response expected.
                        sleeptime=self.sleeptime # reset sleeptime
                    else: # send a command
                        r=self.serialCommsFunction(cmds[i]+self.queryTerminator,self.responseTerminator,maxlen,self.params['min_response_length'],sleeptime)
                        if r is not None: resp+=r # append response
                rawData.append(resp)
            else: 
                # Only one command sent per value
                rawData.append(self.serialCommsFunction(self.serialQuery[n]+self.queryTerminator,\
                               self.responseTerminator,self.maxlen,self.params['min_response_length'],self.sleeptime))
           
        # Convert and store in lastValue
        self.lastValue = self.convert_raw_string_to_values(rawData,self.serialQuery)

        return

    ########################################################################################################################
    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.Serial)
            if self.Serial is None: raise pyLabDataLoggerIOError("Could not access serial port.")
        except:
            print "Serial connection to the device is not open."

        # If first time or reset, get configuration
        if not 'raw_units' in self.params.keys() or reset:
            self.configure_device()

        # Read values        
        self.get_values()
        if self.lastValue is None: self.lastValue=[np.nan]*self.params['n_channels']
	
        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            elif isinstance(v, basestring): lastValueSanitized.append(np.nan) 
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue
