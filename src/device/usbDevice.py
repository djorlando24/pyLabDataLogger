#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    USB device support functions for pyLabDataLogger.
    - Find USB supported devices on the bus.
    - Load appropriate drivers for found devices.
    - Handle VID/PID conflicts for devices that use generic serial ports i.e. FTDI chips.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.2
    @date 27/04/2021
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

# Known hardware.
usb_device_table = [

    # Sigrok devices with fixed VID and PID
    {'vid':0x1a86, 'pid':0xe008, 'driver':'sigrok/tenma-72-7730', 'name':'Tenma 72-7730A Multimeter'},
    {'vid':0x1ab1, 'pid':0x04ce, 'driver':'sigrok/rigol-ds', 'name':'Rigol DS Oscilloscope'},
    {'vid':0x08a9, 'pid':0x0014, 'driver':'sigrok/fx2lafw', 'name':'LHT00SU1 logic analyzer'},
    #{'vid':0x1a86, 'pid':0xe008, 'driver':'sigrok/uni-t-ut32x', 'name':'Tenma 72-7712 Thermometer'}, # replaced with usbhid driver
    
    # USBTMC/SCPI devices with fixed VID and PID
    #{'vid':0x1ab1, 'pid':0x04ce, 'driver':'usbtmc/rigol-ds', 'name':'Rigol DS Oscilloscope'}, # not reliable
    {'vid':0x0957, 'pid':0x0407, 'driver':'usbtmc/33220a', 'name':'Agilent 33220A Waveform Generator'},
    {'vid':0x1313, 'pid':0x80f8, 'driver':'usbtmc/thorlabs-tsp01', 'name':'Thorlabs TSP01 Thermometer/Barometer'},
    {'vid':0x1313, 'pid':0x807b, 'driver':'usbtmc/thorlabs-pm', 'name':'Thorlabs PM16 USB power meter'},
    {'vid':0x1ab1, 'pid':0x0642, 'driver':'usbtmc/dg1000z', 'name':'Rigol DG1000Z programmable delay/function generator'},

    # VISA devices with fixed VID and PID
    {'vid':0x3923, 'pid':0x7269, 'driver':'visa/ni6212', 'name':'National Instruments USB-6212 BNC'},
                 
    # Video and audio streaming devices    
    {'vid':0x1b3f, 'pid':0x2008, 'driver':'alsa', 'name':'USB sound card'},
    {'vid':0x1b80, 'pid':0xe302, 'driver':'alsa', 'name':'Video capture card em28xx (audio stream)'},
    {'vid':0x1b80, 'pid':0xe302, 'driver':'v4l2', 'name':'Video capture card em28xx (video stream)'},
    {'vid':0x1b80, 'pid':0xe31d, 'driver':'alsa', 'name':'Video capture card hu3180e (audio stream)'},
    {'vid':0x1b80, 'pid':0xe31d, 'driver':'v4l2', 'name':'Video capture card hu3180e (video stream)'},
    {'vid':0x1c88, 'pid':0x003f, 'driver':'v4l2', 'name':'Video capture card (video stream)'},
    {'vid':0x1c88, 'pid':0x0007, 'driver':'v4l2', 'name':'Video capture card (video stream)'},

    # OpenCV-compatible webcams
    {'vid':0x045e, 'pid':0x00f5, 'driver':'opencv', 'name':'Microsoft Webcam'},
    {'vid':0x1908, 'pid':0x2311, 'driver':'opencv', 'name':'Gembird Webcam'},
    {'vid':0x534d, 'pid':0x2109, 'driver':'opencv', 'name':'HDMI video capture'},
    #{'vid':0x04f2, 'pid':0xb084, 'driver':'opencv', 'name':'Chicony Internal Webcam'},
    #{'vid':0x04f2, 'pid':0xb5d7, 'driver':'opencv', 'name':'Chicony Internal Webcam'},
    
    # Thorlabs cameras supported by the TSI drivers
    {'vid':0x1313, 'pid':0x4001, 'driver':'thorcam', 'name':'Thorlabs Camera'},

    # Specialty drivers with fixed VID and PID
    {'vid':0x09db, 'pid':0x0112, 'driver':'mcc-libusb/mccusb1608G', 'name':'MCC USB-1608GX-2AO ADC'},
    {'vid':0x0ce9, 'pid':0x1000, 'driver':'picotc08/usbtc08', 'name':'Picolog USB TC-08 thermocouple datalogger'},
    {'vid':0x0ce9, 'pid':0x1016, 'driver':'picoscope/picoscope2k', 'name':'Picoscope 2000 Series'},
    {'vid':0x0f7e, 'pid':0x9002, 'driver':'fluke/568', 'name':'Fluke 568 IR Thermometer'},
    {'vid':0x2a72, 'pid':0x0400, 'driver':'omegaSmartProbe', 'name':'Omega Smart Probe (Autodetect)'},
    {'vid':0x1a86, 'pid':0xe008, 'driver':'uni-t/ut32x', 'name':'UT32x or 72-7712 Thermocouple Reader'},
    
    # Multiple devices with same VID and PID are seperated by the serial number as a unique descriptor.
    {'vid':0x0403, 'pid':0xfaf0, 'driver':'pyapt', 'name':'Thorlabs APT motor driver (generic)'},
    {'vid':0x0403, 'pid':0xfaf0, 'driver':'pyapt', 'serial_number':'27501777', 'name':'Thorlabs APT motor driver (X)'},
    {'vid':0x0403, 'pid':0xfaf0, 'driver':'pyapt', 'serial_number':'27250971', 'name':'Thorlabs APT motor driver (Y)'},
        
    # Serial-over-USB devices with fixed VID and PID
    {'vid':0x0416, 'pid':0x5011, 'driver':'tenmaserial/722710', 'name':'Tenma 72-2710 Power Supply'},
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/omega-ir-usb', 'name':'Omega IR-USB', 'manufacturer':'Omega Engineering'},
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/omega-usbh', 'name':'Omega USB-H Pressure Transducer', 'manufacturer':'Omega Engineering'},
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/sd700', 'name':'Extech SD700 Barometric PTH Datalogger'},
    {'vid':0x10c4, 'pid':0xea60, 'driver':'serial/center310', 'name':'CENTER 310 Humidity meter', 'manufacturer':'Silicon Labs'},
    {'vid':0x10c4, 'pid':0xea60, 'driver':'serial/mx5060', 'name':'Metrix MX5060 Multimeter'},
    {'vid':0x0683, 'pid':0x1480, 'driver':'serial/di148', 'name':'DataQ DI-148 ADC'},
    {'vid':0x0403, 'pid':0xbab1, 'driver':'status/sem1600b', 'name':'STATUS SEM1600/B Load Cell Amplifier'},
    
    # Microcontrollers using serial-over-USB
    {'vid':0x2341, 'pid':0x8036, 'driver':'arduino', 'name':'uDuino (Leonardo)'},
    {'vid':0x2341, 'pid':0x0043, 'driver':'arduino', 'name':'Arduino Uno'},
    {'vid':0x16c0, 'pid':0x0483, 'driver':'arduino', 'name':'Teensy uC'},
    {'vid':0x067b, 'pid':0x2303, 'driver':'arduino', 'name':'Arduino via PL2303'},
    
    # Devices using generic Serial-to-USB adapters whose VID and PID are not correlated specifically to a piece of hardware
    {'vid':0x0557, 'pid':0x2008, 'driver':'serial/ohaus7k', 'name':'OHAUS Valor 7000 scale (RS232)'},
    {'vid':0x0408, 'pid':0x6051, 'driver':'arduino', 'name':'Arduino Pro via FTDI FT231X'},
    {'vid':0x0403, 'pid':0x6015, 'serial':'DB00VHJZ', 'driver':'serial/tds220gpib', 'name':'Tektronix TDS220 via usb-GPIB'},
    {'vid':0x0403, 'pid':0x6015, 'serial':0x3, 'driver':'serial/p6000a', 'name':'Newport P6000A Freq Counter'},
    {'vid':0x067b, 'pid':0x2303, 'driver':'serial/tc08rs232', 'name':'Picolog RS-232 TC-08 thermocouple datalogger'},
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/pt200m', 'name':'PT Ltd. PT200M Load Cell'},
    {'vid':0x0403, 'pid':0x6015, 'driver':'serial/alicat', 'name':'Alicat Scientific M-series mass flow meter'},
    #{'vid':0x1a86, 'pid':0x7523, 'driver':'serial/alicat', 'name':'Alicat Scientific M-series mass flow meter'},
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/wtb', 'name':'Radwag WTB series precision balance'},
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/esd508', 'name':'Leadshine ES-D508 easy servo driver'},
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/r5000', 'name':'Ranger 5000 Load Cell Amplifier'},
    {'vid':0x1a86, 'pid':0x7523, 'driver':'serial/k3hb/vlc', 'name':'Omron K3HB-VLC Load Cell Amplifier'},
    {'vid':0x1a86, 'pid':0x7523, 'driver':'serial/k3hb/x', 'name':'Omron K3HB-X Ammeter'},
    #{'vid':0x0403, 'pid':0x6001, 'driver':'serial/omega-iseries/485', 'name':'Omega iSeries via RS-485'}, # needs work
    #{'vid':0x1a86, 'pid':0x7523, 'driver':'serial/omega-iseries/232', 'name':'Omega iSeries via RS-232'}, # needs work

    # Known but unsupported or generic
    #{'vid':0x1d6b, 'pid':0x0104, 'driver':'beaglebone', 'name':'Beaglebone Black'},
    #{'vid':0x0403, 'pid':0x6015, 'serial':'DB00VHJZ', 'driver':'serial/gpib', 'name':'GPIB-USB adapter'},
    #{'vid':0x067b, 'pid':0x2303, 'driver':'arduino', 'name':'Generic USB to serial cable'},
    #{'vid':0x1a86, 'pid':0x7523, 'driver':'arduino', 'name':'Generic USB to serial cable'},
    #{'vid':0x0403, 'pid':0x6001, 'driver':'arduino', 'name':'FTDI USB to Serial'},
    #{'vid':0x0403, 'pid':0x6015, 'driver':'arduino', 'name':'FTDI USB to Serial'},
    #{'vid':0x10c4, 'pid':0xea60, 'driver':'arduino', 'name':'CP2102 USB to Serial'},
    #{'vid':0x04b4, 'pid':0x0006, 'driver':'arduino', 'name':'Cypress CY7C65213 USB to Serial'},
    #{'vid':0x04b4, 'pid':0xf139, 'driver':'arduino', 'name':'Cypress PSoC5LP'},
    #{'vid':0x2b04, 'pid':0xc006, 'driver':'arduino', 'name':'Particle Photon'},
    #{'vid':0x0525, 'pid':0xa4aa, 'driver':'shell', 'name':'C.H.I.P. (CDC composite gadget)'},
    #{'vid':0x10c4, 'pid':0xea60, 'driver':'shell', 'serial_number':'0001', 'name':'Onion Omega2+'},
    #{'vid':0x0403, 'pid':0x6001, 'driver':'shell', 'bcdDevice':0x600, 'name':'Intel Edison A502OTFN'},
]

from termcolor import cprint

# Search table for a match
def match_device(dev):
    matches=[]
    for match in usb_device_table:
        # Find matching VID and PID (mandatory)
        if (dev.idVendor == match['vid']) and (dev.idProduct == match['pid']):
            matching=True
            # Match optionals
            for key in ['bcdDevice','serial_number','manufacturer']:
                if key in match.keys():
                    if match[key] != get_property(dev,key):
                        matching=False
                        #print(match[key], get_property(dev,key))
                    elif match[key] is None: matching=True
            if matching: matches.append(match)
    return matches

# Get device property, catch exception if not possible.
def get_property(dev,key):
    try:
        return getattr(dev,key)
    except ValueError:
        return None
    except AttributeError:
        return None

# scan USB busses on current machine for matching devices.
def search_for_usb_devices(debugMode=False):
    try:
        import usb.core
    except ImportError as e:
        cprint( "Please install pyUSB", 'red', attrs=['bold'])
        print('\t',e)
        return []

    cprint( "Scanning for USB devices..." ,'cyan')
    found_entries = []

    # Search all USB devices on the computer
    for dev in usb.core.find(find_all=True):
        # Get properties 
        manufacturer = get_property(dev,'manufacturer')
        serial_number = get_property(dev,'serial_number')
        if debugMode:
            print('bus=%03i address=%03i : vid=0x%04x pid=0x%04x : class=0x%02x device=0x%04x manufacturer=%s serial_number=%s' %\
             (dev.bus, dev.address, dev.idVendor, dev.idProduct,dev.bDeviceClass,dev.bcdDevice,manufacturer,serial_number))

        # Check if device is a match with any in the supported devices table
        found_devices = match_device(dev)

        # If multiple matches of the same driver name, take the most specific one.
        if len(found_devices)>1:
            nattrs = [ len(d) for d in found_devices ]
            ndrvrs = [ d['driver'] for d in found_devices ]
            def checkEqualIvo(lst):
                return not lst or lst.count(lst[0]) == len(lst)
            if checkEqualIvo([ d['driver'] for d in found_devices ]):
                found_devices = [found_devices[nattrs.index(max(nattrs))]]

        if len(found_devices) == 0: table_entry = None                  # Found nothing
        elif len(found_devices) == 1: table_entry = found_devices[0]    # Found one device
        elif (len(found_devices) == 2) & ('v4l2' in [d['driver'] for d in found_devices]): table_entry = found_devices # Video and audio capture type device with two drivers
        else:
            # Handle multiple possible matches (generic/common USB adapter)
            print( '\nGeneric USB adapter found at %i.%i. Please choose which hardware you have on this adapter:' % (dev.bus, dev.address) )
            print( "0) None (don't use this device)")
            n=1; choose_n=-1
            for d in found_devices: 
                print( '%i) %s (%s)' % (n,d['name'],d['driver']))
                n+=1
            while (choose_n<0) | (choose_n>len(found_devices)):
                try:
                    choose_n = int(input('> '))
                except ValueError:
                    choose_n = -1
                if choose_n == 0: table_entry = None
                elif choose_n <= len(found_devices): table_entry = found_devices[choose_n-1]
            
        # If matching device(s) found, add to found_entries list

        # Add multiple devices to list
        if isinstance(table_entry, list):
            for n in range(len(table_entry)):
                table_entry[n]['manufacturer']=manufacturer
                table_entry[n]['serial_number']=dev._serial_number
                table_entry[n]['bus']=dev.bus
                table_entry[n]['address']=dev.address
                table_entry[n]['port_numbers']=dev.port_numbers
                print( '- found %s, driver=%s' % (table_entry[n]['name'],table_entry[n]['driver']) )
            found_entries.extend(table_entry)
        # or add one device to list
        elif table_entry is not None:
            table_entry['manufacturer']=manufacturer
            table_entry['serial_number']=dev._serial_number
            table_entry['bus']=dev.bus
            table_entry['address']=dev.address
            table_entry['port_numbers']=dev.port_numbers
            print( '- found %s, driver=%s' % (table_entry['name'],table_entry['driver']) )
            found_entries.append(table_entry)
        

    cprint( 'Detected %i devices.\n' % len(found_entries), 'green')
    return found_entries

"""
	Load up USB devices detected.
	Any driver needing special options can pass them via kwargs.
"""
def load_usb_devices(devs=None,**kwargs):
    device_list=[]
    if devs is None: devs=search_for_usb_devices()

    cprint( '\nLoading drivers...', 'green')
    for d in devs:
        cprint( '\n' + d['name'] + '-' + d['driver'], 'magenta', attrs=['bold'] )
        driverClass = d['driver'].split('/')[0].lower()

        # USB serial types -- load appropriate top level driver here.
        if driverClass == 'tenmaserial':
            from pyLabDataLogger.device import tenmaSerialDevice
            device_list.append(tenmaSerialDevice.tenmaPowerSupplySerialDevice(params=d,**kwargs))
        elif driverClass == 'serial':
            from pyLabDataLogger.device import serialDevice
            device_list.append(serialDevice.serialDevice(params=d,**kwargs))
        elif driverClass == 'arduino':
            from pyLabDataLogger.device import arduinoDevice
            device_list.append(arduinoDevice.arduinoSerialDevice(params=d,**kwargs))
        elif driverClass == 'sigrok':
            from pyLabDataLogger.device import sigrokUsbDevice
            device_list.append(sigrokUsbDevice.srdevice(params=d,**kwargs))
        elif driverClass == 'pyapt':
            from pyLabDataLogger.device import pyAPTDevice
            device_list.append(pyAPTDevice.pyAPTDevice(params=d,**kwargs))
        elif driverClass == 'picotc08':
            from pyLabDataLogger.device import picotc08Device
            device_list.append(picotc08Device.usbtc08Device(params=d,**kwargs))
        elif driverClass == 'alsa':
            from pyLabDataLogger.device import alsaDevice
            device_list.append(alsaDevice.alsaDevice(params=d,**kwargs))
        elif driverClass == 'v4l2':
            from pyLabDataLogger.device import v4l2Device
            device_list.append(v4l2Device.v4l2Device(params=d,**kwargs))
        elif driverClass == 'usbtmc':
            from pyLabDataLogger.device import usbtmcDevice
            device_list.append(usbtmcDevice.usbtmcDevice(params=d,**kwargs))
        elif driverClass == 'mcc-libusb':
            from pyLabDataLogger.device import mcclibusbDevice
            device_list.append(mcclibusbDevice.mcclibusbDevice(params=d,**kwargs))
        elif driverClass == 'fluke':
            from pyLabDataLogger.device import flukeusbDevice
            device_list.append(flukeusbDevice.flukeusbDevice(params=d,**kwargs))
        elif driverClass == 'opencv':
            from pyLabDataLogger.device import opencvDevice
            device_list.append(opencvDevice.opencvDevice(params=d,**kwargs))
        elif driverClass == 'thorcam':
            from pyLabDataLogger.device import thorcamDevice
            device_list.append(thorcamDevice.thorcamDevice(params=d,**kwargs))
        elif driverClass == 'status':
            from pyLabDataLogger.device import statusDevice
            device_list.append(statusDevice.statusDevice(params=d,**kwargs))
        elif driverClass == 'omegasmartprobe':
            from pyLabDataLogger.device import omegaSmartProbeDevice
            device_list.append(omegaSmartProbeDevice.omegaSmartProbeDevice(params=d,**kwargs))
        elif driverClass == 'uni-t':
            from pyLabDataLogger.device import uniTDevice
            device_list.append(uniTDevice.uniTDevice(params=d,**kwargs))
            
        else:
            cprint( "\tI don't know what to do with this device" ,'red', attrs=['bold'])

    return device_list

