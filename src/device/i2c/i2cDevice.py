"""
    I2C device class - for Linux
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2.2
    @date 10/02/2022
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

from ..device import device
from ..device import pyLabDataLoggerIOError
import datetime, time
import numpy as np
from termcolor import cprint

""" Scan for available i2c addresses that may contain
    devices we can talk to. """
def scan_for_devices(bus=1):
    try:
        import smbus
        bus = smbus.SMBus(bus) # 1 indicates /dev/i2c-1
    except ImportError:
        cprint( "Error, smbus module could not be loaded", 'red', attrs=['bold'])
        return
    
    devices=[]
    for device in range(128):
       try:
           bus.read_byte(device)
           devices.append(device)
       except OSError:
           continue
    return devices

""" Load devices based on a-priori knowledge of what addresses on the bus
    correspond to what supported hardware. This won't work for devices that
    share addresses.
    
    Supported devices:
        Adafruit ads1x15 ADCs
        Adafriut BMP085 and BMP150 pressure sensors
        MCP3424 18-Bit ADC-4 Channel with Programmable Gain Amplifier
        DS3231 real-time clock
        Gravity SEN0322 Oxygen sensor

    Future support for:
        CCS811 Air quality sensor

    """
    
# Devices that can be logged.
i2c_input_device_table = [

    # Devices with fixed addresses
    {'address':0x68, 'driver':'ds3231', 'name':'DS3231 Real-time Clock'},\
    {'address':0x77, 'driver':'bmp', 'name':'BMP085/BMP180 barometric pressure sensor'},\
    {'address':0x29, 'driver':'tsl2591', 'name':'TSL2591 light sensor'},\
    {'address':0x33, 'driver':'mlx90640', 'name':'MLX90640 thermal camera'},\
    {'address':0x29, 'driver':'apds9960', 'name':'APDS9960 RGB gesture sensor'},\
    {'address':0x29, 'driver':'vl6180x', 'name':'VL6180X time of flight sensor'},\
    {'address':0x48, 'driver':'lm75a', 'name':'LM75A temperature sensor'}, \
    {'address':0x28, 'driver':'m32jm', 'name':'TE M32JM pressure transducer'},\
    {'address':0xff, 'driver':'max30105', 'name':'MAX30105 dust and particle sensor'}, #0x57 \
    {'address':0x00, 'driver':'lwlp5000', 'name':'LWLP5000 pressure sensor'}, \
        
    # Devices that have multiple addresses
    {'address':[0x76,0x77], 'driver':'ms5611', 'name':'MS5611 barometric pressure sensor'}, #0x76-0x77 \ 
    {'address':0x40, 'driver':'ina226', 'name':'INA226 current sensor'}, #0x40-4f \
    {'address':0x40, 'driver':'ina219', 'name':'INA219 current sensor'}, #0x40,41,44,45 \
    {'address':0x60, 'driver':'mcp9600', 'name':'MCP9600 thermocouple'}, #0x60-67 \
    {'address':(0x48,0x49), 'driver':'tmp117', 'name':'TMP117 temperature sensor'}, #0x48-49 \
    {'address':0xff, 'driver':'mpx5700ap', 'name':'MPX5700 air pressure sensor'}, # 4 unknown addresses \

    {'address':(0x38,0x39), 'driver':'aht10', 'name':'AHT10 temperature and humidity sensor'}, #0x38-0x39 \    
    {'address':(0x18,0x19), 'driver':'lis331', 'name':'H3LIS331DL accelerometer'}, #0x18-0x19 \
    {'address':(0x28,0x29), 'driver':'bno055', 'name':'BNO055 orientation sensor'}, #0x28-0x29 \
    {'address':(0x48,0x49), 'driver':'ads1x15', 'name':'ADS1x15 ADC'},   #0x48-0x49 \
    {'address':(0x5a,0x5b), 'driver':'ccs811', 'name':'CCS811 Air quality sensor'}, #0x5a-0x5b \
    {'address':(0x71,0x72,0x73), 'driver':'dfoxy', 'name':'DFRobot Oxygen Sensor'},    # 0x70-0x73 \
    {'address':(0x6a,0x6c,0x6e), 'driver':'mcp3424', 'name':'MCP3424 18-bit ADC'}, # 0x6a/c/e \
    
]


# Devices we can print output to
i2c_output_device_table = [

    {'address':0x70, 'driver':'fourLetterPHAT'},\
    {'address':0x70, 'driver':'HT16K33 alphanumeric display'},\
    {'address':0xe0, 'driver':'8 digital 7 segment display'}, #0xe0,2,4,6\
        
]
    
# The default i2c bus is 1, which is the external bus on a Raspberry Pi.
# On a desktop PC, this may not be correct - your motherboard may be using bus 1 for CPU temperatures and fan speeds, etc.
# Use the `i2cdetect' tool in Linux to determine the correct bus number.
#
# You can use the addresses keyword to specify an i2c address to force-load
def load_i2c_devices(addresses=None,bus=1,**kwargs):
    if 'quiet' in kwargs: quiet=kwargs['quiet']
    else: quiet=False

    if addresses is None: addresses=scan_for_devices(bus)
    device_list=[]
    
    for a in addresses:
        # Find matches for input devices.
        matches = []
        for d in i2c_input_device_table:
            if isinstance(d['address'],tuple):
                for dd in d['address']:
                    if dd==a: matches.append(d)
            else:
                if d['address']==a: matches.append(d)
        
        if len(matches)>1:
            # Handle multiple matches (addresses are often overlappng between devices)
            print( "\nMultiple IIC devices share the address %s. Please select which driver to use on bus %i:" % (hex(a),bus))
            print( "0) None (don't use this device)")
            n=1; choose_n=-1
            for d in found_devices:
                print( '%i) %s (%s)' % (n,d['name'],d['driver']))
                n+=1
            while (choose_n<0) | (choose_n>len(matches)):
                try:
                    choose_n = int(input('> '))
                except ValueError:
                    choose_n = -1
                if choose_n == 0: continue
                elif choose_n <= len(matches): matches=[matches[choose_n-1]]

        if len(matches)==0:
            continue

        if not quiet:
            if len(device_list)==0: cprint("IIC: Found input devices:",'cyan')
            print('\t',hex(a),matches)

        if matches[0]['driver']=='ccs811':
           from pyLabDataLogger.device.i2c import ccs811Device
           device_list.append(ccs811Device.ccs811Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver']},**kwargs))

        elif matches[0]['driver']=='mcp3424':
            from pyLabDataLogger.device.i2c import mcp3424Device
            device_list.append(mcp3424Device.mcp3424Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver']},**kwargs))

        elif matches[0]['driver']=='ads1x15':
            from pyLabDataLogger.device.i2c import ads1x15Device
            device_list.append(ads1x15Device.ads1x15Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver']},**kwargs))
        
        elif matches[0]['driver']=='bmp':
            from pyLabDataLogger.device.i2c import bmpDevice
            device_list.append(bmpDevice.bmpDevice(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver']},**kwargs))
        
        elif matches[0]['driver']=='dfoxy':
            from pyLabDataLogger.device.i2c import dfoxyDevice
            device_list.append(dfoxyDevice.dfoxyDevice(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver']},**kwargs))

        else:
            raise RuntimeError("Unknown device: %s" % str(matches[0]))

        ''' 
        elif matches[0]['driver']=='ds3231':
            from pyLabDataLogger.device.i2c import ds3231Device
            device_list.append(ds3231.ds3231Device(params={'address':a, 'bus':bus},**kwargs))
        '''


    
    return device_list



########################################################################################################################
class i2cDevice(device):
    """ Class providing support for I2C devices. This class should not be used directly, it provides
        common functions for specific i2c devices. """

    def __init__(self,params={},bus=1,quiet=True,**kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = params # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "untitled I2C device"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        
        # Default I2C bus parameters.
        # The default i2c bus is 1, which is the external bus on a Raspberry Pi.
        # On a desktop PC, this may not be correct - your motherboard may be using bus 1 for CPU temperatures and fan speeds, etc.
        # Use the `i2cdetect' tool in Linux to determine the correct bus number.
        if not 'bus' in params.keys(): params['bus']=bus
        
        # apply kwargs to params
        for k in ['differential','gain']:
           if k in kwargs: self.params[k]=kwargs[k]
        # apply kwargs to config
        for k in ['channel_names']:
           if k in kwargs: self.config[k]=kwargs[k]
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet
        
        if params is {}: return
        self.scan(quiet=self.quiet)
        return

    # Detect if a device is present on bus
    def scan(self,override_params=None,quiet=False):
        if override_params is not None: self.params = override_params
        
        if not 'address' in self.params.keys():
            cprint( "Error, no I2C address specified", 'red', attrs=['bold'])
            return
        
        try:
            import smbus
            bus = smbus.SMBus(self.params['bus'])
            try:
                #bus.read_byte(int(self.params['address'],16))
                bus.read_byte(self.params['address'])
            except:
                cprint( "Error, no I2C devices found on bus %i address %s" % (self.params['bus'],self.params['address']), 'red', attrs=['bold'])
                raise
                return

            self.activate()
            self.query()
            if not quiet: self.pprint()
            
        except ImportError:
            cprint( "Error, smbus module could not be loaded", 'red', attrs=['bold'])
            return
