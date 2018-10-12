"""
    Generic device class - a template for making new devices
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 12/10/2018
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
import atexit

try:
    import usbtc08
except ImportError:
    print "Please install usbtc08"
    raise

########################################################################################################################
# Code in this block adapted from the usbtc08_logger example.
class usbtc08_error(Exception):
    em = {
        usbtc08.USBTC08_ERROR_OK: "No error occurred.",
        usbtc08.USBTC08_ERROR_OS_NOT_SUPPORTED: "The driver does not support the current operating system.",
        usbtc08.USBTC08_ERROR_NO_CHANNELS_SET: "A call to usb_tc08_set_channel() is required.",
        usbtc08.USBTC08_ERROR_INVALID_PARAMETER: "One or more of the function arguments were invalid.",
        usbtc08.USBTC08_ERROR_VARIANT_NOT_SUPPORTED: "The hardware version is not supported. Download the latest driver.",
        usbtc08.USBTC08_ERROR_INCORRECT_MODE: "An incompatible mix of legacy and non-legacy functions was called (or usb_tc08_get_single() was called while in streaming mode.)",
        usbtc08.USBTC08_ERROR_ENUMERATION_INCOMPLETE: "Function usb_tc08_open_unit_async() was called again while a background enumeration was already in progress.",
        usbtc08.USBTC08_ERROR_NOT_RESPONDING: "Cannot get a reply from a USB TC-08.",
        usbtc08.USBTC08_ERROR_FW_FAIL: "Unable to download firmware.",
        usbtc08.USBTC08_ERROR_CONFIG_FAIL: "Missing or corrupted EEPROM.",
        usbtc08.USBTC08_ERROR_NOT_FOUND: "Cannot find enumerated device.",
        usbtc08.USBTC08_ERROR_THREAD_FAIL: "A threading function failed.",
        usbtc08.USBTC08_ERROR_PIPE_INFO_FAIL: "Can not get USB pipe information.",
        usbtc08.USBTC08_ERROR_NOT_CALIBRATED: "No calibration date was found.",
        usbtc08.USBTC08_EROOR_PICOPP_TOO_OLD: "An old picopp.sys driver was found on the system.",
        usbtc08.USBTC08_ERROR_PICO_DRIVER_FUNCTION: "Undefined error.",
        usbtc08.USBTC08_ERROR_COMMUNICATION: "The PC has lost communication with the device."}

    def __init__(self, err = None, note = None):
        self.err = err
        self.note = note
        self.msg = ''
        if err is None:
            self.msg = note
        else:
            if type(err) is int:
                if err in self.em:
                    self.msg = "%d: %s" % (err, self.em[err])
                else:
                    self.msg = "%d: Unknown error" % err
            else:
                self.msg = err
            if note is not None:
                self.msg = "%s [%s]" % (self.msg, note)

    def __str__(self):
        return self.msg


class usbtc08_logger():
    def __init__(self,channel_config,channel_name,unit,debug=True):
        self.debugMode=debug
        self.channel_config=channel_config
        self.self.channel_name=self.channel_name
        self.unit = unit
        self.self.units = {
            usbtc08.USBTC08_selfS_CENTIGRADE : self.self.unit_celsius,
            usbtc08.USBTC08_selfS_FAHRENHEIT : self.self.unit_fahrenheit,
            usbtc08.USBTC08_selfS_KELVIN : self.self.unit_kelvin,
            usbtc08.USBTC08_selfS_RANKINE : self.self.unit_rankine}
        atexit.register(self.close_self)
        self.info = usbtc08.USBTC08_INFO()
        self.info.size = usbtc08.sizeof_USBTC08_INFO
        self.charbuffer = usbtc08.charArray(usbtc08.USBTC08_MAX_INFO_CHARS)
        self.channelbuffer = usbtc08.floatArray(usbtc08.USBTC08_MAX_CHANNELS + 1)
        self.tempbuffer = usbtc08.floatArray(usbtc08.USBTC08_MAX_SAMPLE_BUFFER)
        self.timebuffer = usbtc08.intArray(usbtc08.USBTC08_MAX_SAMPLE_BUFFER)
        self.flags = usbtc08.shortArray(1)
        # Print header to console
        if self.debugMode:
            print '-------------------------------------------'
            print 'Pico Technology USB-TC08 logger'
            print '-------------------------------------------'
        # Settings
        self.self.units[self.unit]()
        # Start communication with device
        self.open_unit_async()
        self.open_unit_progress()
        self.get_unit_info2()
        self.config()

    def config(self):
        for i in self.channel_config:
            self.set_channel(i, self.channel_config.get(i))
        self.set_mains(MAINS)

    def test(self):
        print 'Entered test function.'
        #self.get_self_info()
        #self.get_self_info2()
        self.get_formatted_info()
        self.get_single()

    def clear_data(self):
        self.data = []
        for i in range(0, usbtc08.USBTC08_MAX_CHANNELS + 1):
            self.data.append(OrderedDict())
            map(line.clear, self.lines)

    def process_data(self, channel, samples):
        if self.debugMode:
            print 'Processing %i samples of channel %i.' % (samples, channel)
        if samples > 0:
            time_data = []
            temp_data = []
            for i in range(0, samples):
                time_data.append(self.timebuffer[i] / 1000.0)
                temp_data.append(self.tempbuffer[i])
            new_data = OrderedDict(zip(time_data, temp_data))
            self.data[channel].update(new_data)
            self.lines[channel].add(new_data)
            if min(new_data.values()) < self.plotrangemin:
                self.plotrangemin = max(new_data.values())
            if max(new_data.values()) > self.plotrangemax:
                self.plotrangemax = max(new_data.values())
            plt.ylim(self.plotrangemin * 0.95, self.plotrangemax * 1.05)
            return max(time_data)
        return 0

    def configuration_data(self):
        f=[]
        f.append('Pico Technology TC-08 thermocouple data logger\n')
        f.append('Driver version: {!s}\n'.format(self.info_driver))
        f.append('Kernel driver version: {!s}\n'.format(self.info_kernel))
        f.append('Hardware version: {!s}\n'.format(self.info_hardware))
        f.append('Variant: {!s}\n'.format(self.info_variant))
        f.append('Serial: {!s}\n'.format(self.info_serial))
        f.append('Calibration date: {!s}\n'.format(self.info_calibration))
        f.append('Max sample interval: {:d} ms\n'.format(self.get_minimum_interval_ms()))
        f.append('Used sample interval: {:d} ms\n'.format(self.interval))
        return f

    def open_unit_async(self):
        result = usbtc08.usb_tc08_open_self_async()
        if result == 1:
            if self.debugMode:
                print 'Started enumerating USB TC-08 self.units.'
        elif result == 0:
            if self.debugMode:
                print 'ERROR: No more USB TC-08 self.units found.'
            sys.exit(1)
        elif result == -1:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(0), 'Failed to start enumerating.')

    def open_unit_progress(self):
        result, self.handle, progress = usbtc08.usb_tc08_open_unit_progress()
        while result == usbtc08.USBTC08_PROGRESS_PENDING:
            time.sleep(0.1);
            result, self.handle, progress = usbtc08.usb_tc08_open_unit_progress()
        if result == usbtc08.USBTC08_PROGRESS_FAIL:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(0), 'Waiting completion of enumeration.')
        elif self.handle <= 0:
            if self.debugMode:
                print 'ERROR: No TC-08 self.units detected.'
            sys.exit(1)
        elif result == usbtc08.USBTC08_PROGRESS_COMPLETE:
            if self.debugMode:
                print 'Completed enumeration.'

    def get_self_info(self):
        result = usbtc08.usb_tc08_get_self_info(self.handle, self.info)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Reading self.unit info.')
        else:
            if self.debugMode:
                print 'Received information about the USB TC-08 self.unit.'
        if self.debugMode:
            print 'Driver version: %s' % ''.join(chr(i) for i in self.info.DriverVersion if i in range(32, 127))
            print 'Picopp version: %i' % self.info.PicoppVersion
            print 'Hardware version: %i' % self.info.HardwareVersion
            print 'Variant: %i' % self.info.Variant
            print 'Serial number: %s' % ''.join(chr(i) for i in self.info.szSerial if i in range(32, 127))
            print 'Calibration date: %s' % ''.join(chr(i) for i in self.info.szCalDate if i in range(32, 127))

    def get_self_info2(self):
        result = usbtc08.usb_tc08_get_self_info2(self.handle, self.charbuffer, usbtc08.USBTC08_MAX_VERSION_CHARS, usbtc08.USBTC08LINE_DRIVER_VERSION)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Reading driver version.')
        else:
            length = result
            self.info_driver = ''.join(chr(self.charbuffer[i]) for i in range(0, length) if self.charbuffer[i] in range(32, 127))
            if self.debugMode:
                print 'Driver version: %s' % self.info_driver
        result = usbtc08.usb_tc08_get_self_info2(self.handle, self.charbuffer, usbtc08.USBTC08_MAX_VERSION_CHARS, usbtc08.USBTC08LINE_KERNEL_DRIVER_VERSION)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Reading kernel driver version.')
        else:
            length = result
            self.info_kernel = ''.join(chr(self.charbuffer[i]) for i in range(0, length) if self.charbuffer[i] in range(32, 127))
            if self.debugMode:
                print 'Kernel driver version: %s' % self.info_kernel
        result = usbtc08.usb_tc08_get_self_info2(self.handle, self.charbuffer, usbtc08.USBTC08_MAX_VERSION_CHARS, usbtc08.USBTC08LINE_HARDWARE_VERSION)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Reading hardware version.')
        else:
            length = result
            self.info_hardware = ''.join(chr(self.charbuffer[i]) for i in range(0, length) if self.charbuffer[i] in range(32, 127))
            if self.debugMode:
                print 'Hardware version: %s' % self.info_hardware
        result = usbtc08.usb_tc08_get_self_info2(self.handle, self.charbuffer, usbtc08.USBTC08_MAX_INFO_CHARS, usbtc08.USBTC08LINE_VARIANT_INFO)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Reading variant info.')
        else:
            length = result
            self.info_variant = ''.join(chr(self.charbuffer[i]) for i in range(0, length) if self.charbuffer[i] in range(32, 127))
            if self.debugMode:
                print 'Variant info: %s' % self.info_variant
        result = usbtc08.usb_tc08_get_self_info2(self.handle, self.charbuffer, usbtc08.USBTC08_MAX_SERIAL_CHARS, usbtc08.USBTC08LINE_BATCH_AND_SERIAL)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Reading batch and serial.')
        else:
            length = result
            self.info_serial = ''.join(chr(self.charbuffer[i]) for i in range(0, length) if self.charbuffer[i] in range(32, 127))
            if self.debugMode:
                print 'Batch and serial: %s' % self.info_serial
        result = usbtc08.usb_tc08_get_self_info2(self.handle, self.charbuffer, usbtc08.USBTC08_MAX_DATE_CHARS, usbtc08.USBTC08LINE_CAL_DATE)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Reading calibration date.')
        else:
            length = result
            self.info_calibration = ''.join(chr(self.charbuffer[i]) for i in range(0, length) if self.charbuffer[i] in range(32, 127))
            if self.debugMode:
                print 'Calibration date: %s' % self.info_calibration

    def get_formatted_info(self):
        result = usbtc08.usb_tc08_get_formatted_info(self.handle, self.charbuffer, usbtc08.USBTC08_MAX_INFO_CHARS)
        if result == 0:
            if self.debugMode:
                print 'ERROR: Too many bytes to copy.'
        else:
            if self.debugMode:
                print 'Formatted self.unit info: \n%s' % ''.join(chr(self.charbuffer[i]) for i in range(0, usbtc08.USBTC08_MAX_INFO_CHARS))

    def set_channel(self, channel, tc):
        result = usbtc08.usb_tc08_set_channel(self.handle, channel, ord(tc))
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Setting channel.')
        else:
            if self.debugMode:
                print 'Set channel %i to %s-type thermocouple.' % (channel, tc)

    def disable_channel(self, channel):
        result = usbtc08.usb_tc08_set_channel(self.handle, channel, ord(' '))
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Disabling channel.')
        else:
            if self.debugMode:
                print 'Disabled channel %i.' % (channel)

    def set_mains(self, freq):
        if freq == 60:
            result = usbtc08.usb_tc08_set_mains(self.handle, 1)
        elif freq == 50:
            result = usbtc08.usb_tc08_set_mains(self.handle, 0)
        else:
            if self.debugMode:
                print 'ERROR: Incorrect mains frequency. Default to filter 50 Hz.'
            result = usbtc08.usb_tc08_set_mains(self.handle, 0)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Setting mains filter.')
        else:
            if self.debugMode:
                print 'Set USB TC-08 self.unit to reject %i Hz.' % freq

    def get_minimum_interval_ms(self):
        result = usbtc08.usb_tc08_get_minimum_interval_ms(self.handle)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Read the minimum sample interval.')
        else:
            interval = result
            if self.debugMode:
                print 'Minimum sampling interval is %i ms.' % interval
        return interval

    def run(self, interval):
        result = usbtc08.usb_tc08_run(self.handle, interval)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Issue run command.')
        else:
            if self.debugMode:
                print 'Started sampling with %i ms interval.' % interval

    def get_temp(self, channel):
        result = usbtc08.usb_tc08_get_temp(self.handle, self.tempbuffer, self.timebuffer, usbtc08.USBTC08_MAX_SAMPLE_BUFFER, self.flags, channel, self.self.unit, 0)
        print 'Received result: %i' % result
        samples = 0
        if result == -1:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Reading data of channel.')
        elif result == 0:
            if self.debugMode:
                print 'No samples available.'
        else:
            samples = result
            if self.debugMode:
                print 'Read %i samples to the buffer.' % samples
        if self.debugMode:
            for i in range(0, samples):
                print '%i %4.2f' % (self.timebuffer[i], self.tempbuffer[i])
            print 'Flags: %s' % "{0:b}".format(self.flags[0]).zfill(9)
        return samples

    def get_temp_deskew(self, channel):
        result = usbtc08.usb_tc08_get_temp_deskew(self.handle, self.tempbuffer, self.timebuffer, usbtc08.USBTC08_MAX_SAMPLE_BUFFER, self.flags, channel, self.self.unit, 0)
        samples = 0
        if result == -1:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Reading deskewed data of channel.')
        elif result == 0:
            if self.debugMode:
                print 'No samples available.'
        else:
            samples = result
            if self.debugMode:
                print 'Read %i samples to the buffer.' % samples
        if self.debugMode:
            for i in range(0, samples):
                print '%i %4.2f' % (self.timebuffer[i], self.tempbuffer[i])
            print 'Flags: %s' % "{0:b}".format(self.flags[0]).zfill(9)
        return samples

    def stop(self):
        result = usbtc08.usb_tc08_stop(self.handle)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Stop sampling.')
        else:
            if self.debugMode:
                print 'Stopped sampling.'

    def get_single(self):
        result = usbtc08.usb_tc08_get_single(self.handle, self.channelbuffer, self.flags, self.self.unit)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Take single measurement of all channels.')
        else:
            if self.debugMode:
                print 'Take a single measurement of all channels.'
                for i in range(0, 9):
                    print 'Channel %i: %4.2f %s' % (i, self.channelbuffer[i], self.self.unit_text)
        if self.debugMode:
            print 'Flags: %s' % "{0:b}".format(self.flags[0]).zfill(9)

    def unit_celsius(self):
        self.self.unit = usbtc08.USBTC08_selfS_CENTIGRADE
        self.self.unit_text = u'°C'
        if self.debugMode:
            print 'self.unit set to %s.' % self.self.unit_text

    def unit_fahrenheit(self):
        self.self.unit = usbtc08.USBTC08_selfS_FAHRENHEIT
        self.self.unit_text = u'°F'
        if self.debugMode:
            print 'self.unit set to %s.' % self.self.unit_text

    def unit_kelvin(self):
        self.self.unit = usbtc08.USBTC08_selfS_KELVIN
        self.self.unit_text = 'K'
        if self.debugMode:
            print 'self.unit set to %s.' % self.self.unit_text

    def unit_rankine(self):
        self.self.unit = usbtc08.USBTC08_selfS_RANKINE
        self.self.unit_text = u'°R'
        if self.debugMode:
            print 'self.unit set to %s.' % self.self.unit_text

    def close_self(self):
        result = usbtc08.usb_tc08_close_self(self.handle)
        if result == 0:
            raise usbtc08_error(usbtc08.usb_tc08_get_last_error(self.handle), 'Closing communication.')
        else:
            if self.debugMode:
                print 'self.unit closed successfully.'

########################################################################################################################
class usbtc08Device(device):
    """ Class providing support for Pico TC-08 thermocouple dataloggers.
        There are RS-232 & USB versions, so far only the USB version is tested.
    """

    def __init__(self,params={},quiet=False):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. self.units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device self.units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "Pico TC-08 Thermocouple Logger"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        if params is not {}: self.scan(quiet=quiet)
        
        return

    # Detect if device is present
    def scan(self,override_params=None,quiet=False):
        
        if override_params is not None: self.params = override_params
        
        # ...
        
        else: self.activate(quiet=quiet)
        return

    # Establish connection to device (ie open serial port)
    def activate(self,quiet=False):
        
        # Channel configurations (Dan's preferred defaults)
        channel_config = {
            usbtc08.USBTC08_CHANNEL_CJC: 'C', # Needs to be 'C'.
            usbtc08.USBTC08_CHANNEL_1: 'K',
            usbtc08.USBTC08_CHANNEL_2: 'K',
            usbtc08.USBTC08_CHANNEL_3: 'K',
            usbtc08.USBTC08_CHANNEL_4: 'T',
            usbtc08.USBTC08_CHANNEL_5: 'T',
            usbtc08.USBTC08_CHANNEL_6: 'T',
            usbtc08.USBTC08_CHANNEL_7: 'X',
            usbtc08.USBTC08_CHANNEL_8: 'X'}
        # Set the name of each channel.
        channel_name = {
            usbtc08.USBTC08_CHANNEL_CJC: 'Cold-junction',
            usbtc08.USBTC08_CHANNEL_1: 'T_K1',
            usbtc08.USBTC08_CHANNEL_2: 'T_K2',
            usbtc08.USBTC08_CHANNEL_3: 'T_K3',
            usbtc08.USBTC08_CHANNEL_4: 'T_T4',
            usbtc08.USBTC08_CHANNEL_5: 'T_T5',
            usbtc08.USBTC08_CHANNEL_6: 'T_T6',
            usbtc08.USBTC08_CHANNEL_7: '420mA_PT1',
            usbtc08.USBTC08_CHANNEL_8: '420mA_PT2'}
        # Set the preferred self.unit of temperature. Options are degC, degF, K and degR.
        unit = usbtc08.USBTC08_selfS_CENTIGRADE
        # usbtc08.USBTC08_selfS_FAHRENHEIT
        # usbtc08.USBTC08_selfS_KELVIN
        # usbtc08.USBTC08_selfS_RANKINE
        
        self.dev = usbtc08_logger(channel_config,channel_name,unit,debugMode=True)
                                    
        # Make first query to get self.units, description, etc.
        self.query(reset=True)

        if not quiet: self.pprint()
        return

    # Deactivate connection to device (close serial port)
    def deactivate(self):
        # ...
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

        # If first time or reset, get configuration (ie self.units)
        if not 'raw_selfs' in self.params.keys() or reset:
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


