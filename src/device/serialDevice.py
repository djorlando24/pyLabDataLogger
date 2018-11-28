"""
    Serial device class - general serial port support
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 28/11/2018
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
import datetime, time, struct, sys

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
    """


    def __init__(self,params={},tty_prefix='/dev/',quiet=False,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "uninitialized"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        self.Serial = None
        self.tty_prefix = tty_prefix
        if 'quiet' in kwargs:
            self.quiet = quiet | kwargs['quiet']
        else:
            self.quiet = quiet
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
            
            from serial.tools import list_ports
            for serialport in list_ports.comports():
                if not 'vid' in dir(serialport):
                    if len(serialport)>0:
                        self.port = serialport[0]
                        if not self.tty_prefix in self.port: self.port = self.tty_prefix + self.port
                        self.params['tty']=self.port
                else:
                    if serialport.vid==self.params['vid'] and serialport.pid==self.params['pid']:
                        if not self.quiet: print '\t',serialport.hwid, serialport.name
                        if serialport.name is not None:
                            self.port = serialport.name # Linux
                        else:
                            self.port = serialport.device # MacOS
                        if not self.tty_prefix in self.port: self.port = self.tty_prefix + self.port
                        self.params['tty']=self.port
                    
        if self.port is None:
            print "\tUnable to connect to serial port - port unknown."
            print "\tYou may need to install a specific USB-to-Serial driver."
            print "\tfound non-matching ports:",list_ports.comports()[0]
        
        else: self.activate()
        return

    ########################################################################################################################
    # Establish connection to device (ie open serial port)
    def activate(self):
    
        # Over-ride serial comms parameters for special devices
        subdriver = ''.join(self.params['driver'].split('/')[1:])
        if subdriver=='omega-iseries':
            if not 'bytesize' in self.params.keys(): self.params['bytesize']=serial.SEVENBITS
            if not 'parity' in self.params.keys(): self.params['parity']=serial.PARITY_EVEN
            if not 'stopbits' in self.params.keys(): self.params['stopbits']=serial.STOPBITS_ONE
            self.params['timeout']=0.5
        
        # Default serial port parameters passed to pySerial
        if not 'baudrate' in self.params.keys(): self.params['baudrate']=9600
        if not 'bytesize' in self.params.keys(): self.params['bytesize']=serial.EIGHTBITS
        if not 'parity' in self.params.keys(): self.params['parity']=serial.PARITY_NONE
        if not 'stopbits' in self.params.keys(): self.params['stopbits']=serial.STOPBITS_ONE
        if not 'xonxoff' in  self.params.keys(): self.params['xonxoff']=False
        if not 'rtscts' in  self.params.keys(): self.params['rtscts']=False
        if not 'timeout' in self.params.keys(): self.params['timeout']=2. # sec for a single byte read/write
        
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
        subdriver = self.params['driver'].split('/')[1:]
        try:
            assert(self.Serial)
            if self.Serial is None: raise IOError

            # Apply subdriver-specific variable writes
            if subdriver=='omega-ir-usb':
                e=self.config['set_emissivity']
                if (e is not None) and (e>0) and (e<=1.): self.Serial.write("E%0.2f\n" % float(e))
                else: raise ValueError
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
            else:
                raise RuntimeError("I don't know what to do with a device driver %s" % self.params['driver'])

        except IOError as e:
            print "\t%s communication error" % self.name
            print "\t",e
        except ValueError:
            print "%s - Invalid set point requested" % self.name
            print "\t(V=",self.params['set_voltage'],"I=", self.params['set_current'],")"
        
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
    def blockingSerialRequest(self,request,terminationChar='\r',maxlen=1024,min_response_length=0):
        s=''
        response=None
        if not self.quiet:
            sys.stdout.write('\t'+self.port+':'+repr(request)+'\t')
            sys.stdout.flush()
        self.Serial.write(request)
        t_=time.time()
        time.sleep(0.01)
        while len(s)<maxlen:
            s+=self.Serial.read(1)
            if len(s) == 0: # response timed out
                break
            if (s[-1] == terminationChar) and (len(s)>min_response_length):
                response=s.strip()
                break
            if (time.time() - t_) > self.params['timeout_total']: raise IOError
        if not self.quiet: sys.stdout.write(repr(response)+'\n')
        return response
    
    ########################################################################################################################
    # Special function to handle reading data that shouldn't have any special characters stripped out.
    # This is useful if the length of the data could be arbitrary and not even whole numbers of bytes,
    # or if the read command doesn't reliably returned buffered data (i.e. for RS-485 where there is
    # some delay for the direction switching)
    def blockingRawSerialRequest(self,request,terminationChar='\r',maxlen=1024,min_response_length=0):
        self.Serial.write(request)
        t_=time.time()
        time.sleep(0.01)
        data=''
        while len(data)<maxlen:
            data += self.Serial.read(1)
            if len(data) > 0:
                if (data[-1] == terminationChar) and (len(data)>min_response_length):
                    break
            if (time.time() - t_) > self.params['timeout_total']: raise IOError
        return data
    
    ########################################################################################################################
    # Configure device based on what sub-driver is being used.
    # This is done when self.query(reset=True) is called, as at
    # this point we might need to poll the device to check a setting.
    def configure_device(self):
    
        subdriver = self.subdriver
        
        # By default, using blockingSerialRequest
        self.serialCommsFunction = self.blockingSerialRequest

        # ----------------------------------------------------------------------------------------
        if subdriver=='omega-ir-usb': # Statup config for IR-USB
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
        elif subdriver=='ohaus7k': # Startup config for OHAUS Valor 7000
            #Get the units currently set on the display
            unit='?'
            try:
                unit=self.blockingSerialRequest('PU\r\n','\r')
                if unit is None: unit='?'
            except IOError:
                # It's ok, we can get this on the query() later
                pass
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
            try:
                self.params['ID']=self.blockingSerialRequest('K\r\n','\r')
                print "\tReturned Model ID =",self.params['ID']
            except IOError as e:
                print "\t%s communication error" % self.name
                print "\t",e
            
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
            self.serialQuery=['*\xb01X\xb01',\
                              '*\xb01R\xb01',\
                              '*\xb01R\xb02',\
                              '*\xb01U\xb01']
            self.queryTerminator='\r'
            self.responseTerminator='\r'
            self.serialCommsFunction=self.blockingRawSerialRequest
            self.params['min_response_length']=1 # bytes
        
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
            if subdriver=='omega-ir-usb':
                if len(rawData)<2: return [None]*self.params['n_channels']
                vals= [float(rawData[0].strip('>')), float(rawData[1].strip('>'))]
                if len(rawData)<3: vals.extend([np.nan, np.nan])
                else: vals.extend([float(v) for v in rawData[2].split('=')[1].split(',')])
                if len(rawData)<4: vals.append(np.nan)
                else: vals.append(float(rawData[3].split('=')[1]))
                return vals

            # ----------------------------------------------------------------------------------------
            elif subdriver=='ohaus7k':
                vals=rawData[0].split(' ')
                self.params['raw_units']=[vals[-1].strip()]
                return [float(vals[0])]

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
                else: 
                    print "\t!! Unknown device mode string in serial response"
                    raise ValueError
                if len(rawData)<6: raise ValueError # Short/corrupted responses.
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
        try:
            rawData=[]
            for n in range(len(self.serialQuery)):
                rawData.append(self.serialCommsFunction(self.serialQuery[n]+self.queryTerminator,\
                        self.responseTerminator,min_response_length=self.params['min_response_length']))
            self.lastValue = self.convert_raw_string_to_values(rawData,self.serialQuery)

        except IOError as e:
            print "\t%s communication error" % self.name
            print "\t",e

        return #[np.nan]*self.params['n_channels']

    ########################################################################################################################
    # Handle query for values
    def query(self, reset=False):

        # Check
        try:
            assert(self.Serial)
            if self.Serial is None: raise IOError
        except:
            print "Serial connection to the device is not open."

        # If first time or reset, get configuration
        if not 'raw_units' in self.params.keys() or reset:
            driver = self.params['driver'].split('/')[1:]
            self.subdriver = driver[0].lower()
            self.configure_device()

        # Read values        
        self.get_values()
	if self.lastValue is None: self.lastValue=[np.nan]*self.params['n_channels']
	
        # Generate scaled values. Convert non-numerics to NaN
        lastValueSanitized = []
        for v in self.lastValue: 
            if v is None: lastValueSanitized.append(np.nan)
            else: lastValueSanitized.append(v)
        self.lastScaled = np.array(lastValueSanitized) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        return self.lastValue
