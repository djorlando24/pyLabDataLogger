#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    I2C device class - for Linux using FTDI Bridge
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 13/06/25

    Multiphase Flow Laboratory
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
import datetime, time, os
import numpy as np
from termcolor import cprint

try:
    import serial
    import i2cdriver
    
except ImportError:
    cprint( "Please install pySerial and i2cdriver", 'red', attrs=['bold'])
    raise

""" Find the serial port of the bridge. 
    This code varies depending on OS, so has some branching logic. """

def locationMatch(serialport,params):
    if ('port_numbers' in params) and ('bus' in params) and ('location' in dir(serialport)):
        search_location = '%i-%s' % (params['bus'],'.'.join(['%i'% nn for nn in params['port_numbers']]))
        if search_location == serialport.location: return True
        elif ((':' not in search_location) and (':' in serialport.location)): # if '2-1' doesn't match '2-1:1.0' for example.
            if search_location in serialport.location: return True
        else:        
            return False
    else:
        # If the feature is unsupported, assume first device is the real one! We can't check.
        return True
    
def findBridgeSerialPort(params):
    from serial.tools import list_ports
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
            if thevid==params['vid'] and thepid==params['pid'] and locationMatch(serialport,params):
                params['tty']=serialport.device
                port=serialport.device

        # if the returned device is a list, tuple or dictionary
        elif len(serialport)>1:

            # Some versions return a dictionary, some return a tuple with the VID:PID in the last string.
            if 'VID:PID' in serialport[-1]: # tuple or list
                thename = serialport[0]
                # Sometimes serialport[-1] will contain "USB VID:PID=0x0000:0x0000" and
                # sometimes extra data will follow after, i.e. "USB VID:PID=1234:5678 SERIAL=90ab".
                vididx = serialport[-1].upper().index('PID')
                if vididx <= 0: raise IndexError("Can't interpret USB VID:PID information!")
                vidpid = serialport[-1][vididx+4:vididx+13] # take fixed set of chars after 'PID='
                thevid,thepid = [ int(val,16) for val in vidpid.split(':')]
                if thevid==params['vid'] and thepid==params['pid'] and locationMatch(serialport,params):

                    if thename is not None:
                        port = thename # Linux
                    else:
                        port = serialport.device # MacOS
                    if not tty_prefix in port: port = tty_prefix + port
                    params['tty']=port

            elif 'vid' in dir(serialport): # dictionary
                if serialport.vid==params['vid'] and serialport.pid==params['pid'] and locationMatch(serialport,params):
                    # Vid/Pid matching
                    if not quiet: print( '\t'+str(serialport.hwid)+' '+str(serialport.name))
                    if serialport.name is not None:
                        port = serialport.name # Linux
                    else:
                        port = serialport.device # MacOS
                    if not tty_prefix in port: port = tty_prefix + port
                    params['tty']=port

        # List or dict with only one entry.
        elif len(list_ports.comports())==1: # only one found, use as default
            port = serialport[0]
            if not tty_prefix in port: port = tty_prefix + port
            params['tty']=port

        if 'tty' in params:
            if os.path.exists(params['tty']): break

    return params 


""" Scan for available i2c addresses that may contain
    devices we can talk to. """
def scan_for_devices(port="/dev/ttyUSB0"):
    i2c = i2cdriver.I2CDriver(port)
    return i2c.scan(silent=True)

    
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
    {'address':0x57, 'driver':'max30105', 'name':'MAX30105 dust and particle sensor'},\
    {'address':0x00, 'driver':'lwlp5000', 'name':'LWLP5000 pressure sensor'}, \
    {'address':0x48, 'driver':'pcf8591', 'name':'PCF8591 8-bit ADC'},\
    {'address':(0x38,0x39), 'driver':'ahtx0', 'name':'AHTx0 temperature and humidity sensor'},\
    {'address':0x5a, 'driver':'mpr121', 'name':'MPR121 capacitative touch sensor'},\

    # Devices that have multiple addresses
    {'address':(0x18,0x19), 'driver':'h3lis331dl', 'name':'H3LIS331DL accelerometer'},\
    {'address':(0x76,0x77), 'driver':'ms5637', 'name':'MS5637 barometric pressure sensor'}, #0x76-0x77 \ 
    {'address':0x40, 'driver':'ina226', 'name':'INA226 current sensor'}, #0x40-4f \
    {'address':0x40, 'driver':'ina219', 'name':'INA219 current sensor'}, #0x40,41,44,45 \
    {'address':0x60, 'driver':'mcp9600', 'name':'MCP9600 thermocouple'}, #0x60-67 \
    {'address':(0x48,0x49), 'driver':'tmp117', 'name':'TMP117 temperature sensor'}, #0x48-49 \
    {'address':0xff, 'driver':'mpx5700ap', 'name':'MPX5700 air pressure sensor'}, # 4 unknown addresses \
    {'address':(0x48,0x49), 'driver':'ads1x15', 'name':'ADS1x15 ADC'},   #0x48-0x49 \
    {'address':(0x5a,0x5b), 'driver':'ccs811', 'name':'CCS811 Air quality sensor'}, #0x5a-0x5b \
    {'address':(0x71,0x72,0x73), 'driver':'dfoxy', 'name':'DFRobot Oxygen Sensor'},    # 0x70-0x73 \
    {'address':(0x6a,0x6c,0x6e), 'driver':'mcp3424', 'name':'MCP3424 18-bit ADC'}, # 0x6a/c/e \
   
    # Not supported well on the Rasberry Pi - requires clock stretching
    {'address':(0x29), 'driver':'bno055', 'name':'BNO055 orientation sensor'},\
    #{'address':0x28, 'driver':'tfmini-lidar', 'name':'TFMini I2C LiDAR ToF Laser Range Sensor'}, # Not required since >1 other device on 0x28 \
]


# Devices we can print output to
i2c_output_device_table = [

    {'address':0x70, 'driver':'fourLetterPHAT'},\
    {'address':0x70, 'driver':'HT16K33 alphanumeric display'},\
    {'address':0xe0, 'driver':'8 digital 7 segment display'}, #0xe0,2,4,6\
        
]
    

def load_i2c_devices(addresses=None,bridgeConfig={},**kwargs):
    if 'quiet' in kwargs: quiet=kwargs['quiet']
    else: quiet=False
    
    bus=None
    if addresses is None: addresses=scan_for_devices(kwargs['tty'])
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
            print( "\nMultiple I2C devices share the address %s. Please select which driver to use:" % (hex(a)))
            print( "0) None (don't use this device)")
            n=1; choose_n=-1
            for d in matches:
                print( '%i) %s (%s)' % (n,d['name'],d['driver']))
                n+=1
            while (choose_n<0) | (choose_n>len(matches)):
                try:
                    choose_n = int(input('> '))
                except ValueError:
                    choose_n = -1
                if choose_n == 0: continue
        
            if choose_n>0: matches=[matches[choose_n-1]]
            else: matches=[]

        if len(matches)==0:
            continue

        if not quiet:
            if len(device_list)==0: cprint("I2C: Found input devices:",'cyan')
            print('\t',hex(a),matches)

        if matches[0]['driver']=='pcf8591':
           from pyLabDataLogger.device.i2c import pcf8591Device
           device_list.append(pcf8591Device.pcf8591Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))
       
        elif matches[0]['driver']=='max30105':
           from pyLabDataLogger.device.i2c import max30105Device
           device_list.append(max30105Device.max30105Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

        elif matches[0]['driver']=='tsl2591':
           from pyLabDataLogger.device.i2c import tsl2591Device
           device_list.append(tsl2591Device.tsl2591Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

        elif matches[0]['driver']=='m32jm':
            from pyLabDataLogger.device.i2c import m32jmDevice
            device_list.append(m32jmDevice.m32jmDevice(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

        elif matches[0]['driver']=='ccs811':
           from pyLabDataLogger.device.i2c import ccs811Device
           device_list.append(ccs811Device.ccs811Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

        elif matches[0]['driver']=='mcp3424':
            from pyLabDataLogger.device.i2c import mcp3424Device
            device_list.append(mcp3424Device.mcp3424Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

        elif matches[0]['driver']=='ads1x15':
            from pyLabDataLogger.device.i2c import ads1x15Device
            device_list.append(ads1x15Device.ads1x15Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))
        
        elif matches[0]['driver']=='bmp':
            from pyLabDataLogger.device.i2c import bmpDevice
            device_list.append(bmpDevice.bmpDevice(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))
        
        elif matches[0]['driver']=='dfoxy':
            from pyLabDataLogger.device.i2c import dfoxyDevice
            device_list.append(dfoxyDevice.dfoxyDevice(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

        elif matches[0]['driver']=='ahtx0':
            from pyLabDataLogger.device.i2c import ahtx0Device
            device_list.append(ahtx0Device.ahtx0Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

        elif matches[0]['driver']=='h3lis331dl':
            from pyLabDataLogger.device.i2c import h3lis331dlDevice
            device_list.append(h3lis331dlDevice.h3lis331dlDevice(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

        elif matches[0]['driver']=='mpr121':
            from pyLabDataLogger.device.i2c import mpr121Device
            device_list.append(mpr121Device.mpr121Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

        elif matches[0]['driver']=='ms5637':
            from pyLabDataLogger.device.i2c import ms5637Device
            device_list.append(ms5637Device.ms5637Device(params={'address':a, 'bus':bus, 'name':matches[0]['name'], 'driver':matches[0]['driver'], 'tty':bridgeConfig['tty']},**kwargs))

       
            
        else:
            raise RuntimeError("Unknown device: %s" % str(matches[0]))

        ''' 
        elif matches[0]['driver']=='ds3231':
            from pyLabDataLogger.device.i2c import ds3231Device
            device_list.append(ds3231.ds3231Device(params={'address':a, 'bus':bus},**kwargs))
        '''


    
    return device_list



