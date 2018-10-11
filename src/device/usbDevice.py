#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    USB device support for pyLabDataLogger.
    - Find USB supported devices on the bus.
    
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

# Known hardware.
usb_device_table = [

    # Sigrok devices with fixed VID and PID
    {'vid':0x1a86, 'pid':0xe008, 'bcdDevice':0x1300, 'driver':'sigrok/uni-t-ut32x', 'name':'Tenma 72-7712 Thermometer'},
    {'vid':0x1a86, 'pid':0xe008, 'bcdDevice':0x1400, 'driver':'sigrok/tenma-72-7730', 'name':'Tenma 72-7730A Multimeter'},
    {'vid':0x1ab1, 'pid':0x04ce, 'driver':'sigrok/rigol-ds', 'name':'Rigol DS Oscilloscope'},
    {'vid':0x08a9, 'pid':0x0014, 'driver':'sigrok/fx2lafw', 'name':'LHT00SU1 logic analyzer'},
                 
    # Specialty drivers with fixed VID and PID
    {'vid':0x1b3f, 'pid':0x2008, 'driver':'alsa', 'name':'USB sound card'},
    {'vid':0x0403, 'pid':0xfaf0, 'driver':'pyapt', 'name':'Thorlabs APT motor driver'},
    {'vid':0x09db, 'pid':0x0112, 'driver':'mcc-libusb/usb-1608g', 'name':'MCC USB-1608GX-2AO ADC'},
    {'vid':0x1313, 'pid':0x807b, 'driver':'thorlabs/pm120', 'name':'Thorlabs PM120'},
    {'vid':0x0000, 'pid':0x9999, 'driver':'usbtc08', 'name':'Picolog USB TC-08 thermocouple datalogger'},
    
    # Serial-over-USB devices with fixed VID and PID
    {'vid':0x0416, 'pid':0x5011, 'driver':'tenmaserial/722710', 'name':'Tenma 72-2710 Power Supply'},
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/omega-ir-usb', 'name':'Omega IR-USB', 'manufacturer':'Omega Engineering'},
    {'vid':0x10c4, 'pid':0xea60, 'driver':'serial/center310', 'name':'CENTER 310 Humidity meter', 'manufacturer':'Silicon Labs'},

    # Microcontrollers using serial-over-USB
    {'vid':0x2341, 'pid':0x8036, 'driver':'arduino', 'name':'uDuino (Leonardo)'},
    {'vid':0x2341, 'pid':0x0043, 'driver':'arduino', 'name':'Arduino Uno'},
    {'vid':0x16c0, 'pid':0x0483, 'driver':'arduino', 'name':'Teensy uC'},
    
    # Devices using RS232/485 to USB adapters whose VID and PID may change depending on the dongle
    {'vid':0x0557, 'pid':0x2008, 'driver':'serial/ohaus7k', 'name':'OHAUS Valor 7000 scale (RS232)'},
    
    # Known but unsupported or generic
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
    #{'vid':0x1d6b, 'pid':0x0104, 'driver':'shell', 'name':'Beaglebone Black'},
    #{'vid':0x0403, 'pid':0x6001, 'driver':'shell', 'bcdDevice':0x600, 'name':'Intel Edison A502OTFN'},
    #{'vid':0x0403, 'pid':0x6001, 'driver':'serial/omega-process-controller', 'name':'FTDI USB to RS485 adapter'},
]



# Search table for a match
def match_device(dev):
    for match in usb_device_table:
        # Find matching VID and PID (mandatory)
        if (dev.idVendor == match['vid']) and (dev.idProduct == match['pid']):
            matching=True
            # Match optionals
            for key in ['bcdDevice','serial_number','manufacturer']:
                if key in match.keys():
                    if match[key] != get_property(dev,key): matching=False
                    elif match[key] is None: matching=True
            if matching: return match
    return None

# Get device property, catch exception if not possible.
def get_property(dev,key):
    try:
        return getattr(dev,key)
    except ValueError:
        return None

# scan USB busses on current machine for matching devices.
def search_for_usb_devices(debugMode=False):
    try:
        import usb.core
    except ImportError as e:
        print "Please install pyUSB"
        print '\t',e
        return []

    print "Scanning for USB devices..."
    found_entries = []
    for dev in usb.core.find(find_all=True):
        if debugMode: 
            manufacturer = get_property(dev,'manufacturer')
            serial_number = get_property(dev,'serial_number')
            print 'bus=%03i address=%03i : vid=0x%04x pid=0x%04x : class=0x%02x device=0x%04x manufacturer=%s serial=%s' %\
             (dev.bus, dev.address, dev.idVendor, dev.idProduct,dev.bDeviceClass,dev.bcdDevice,manufacturer,serial_number)
        table_entry = match_device(dev)
        if table_entry is not None:
            print '- found %s, driver=%s' % (table_entry['name'],table_entry['driver'])
            found_entries.append(table_entry)

    print 'Detected %i devices.\n' % len(found_entries)
    return found_entries

# Load up USB devices detected.
def load_usb_devices(devs=None):
    device_list=[]
    if devs is None: devs=search_for_usb_devices()

    print '\nLoading drivers...'
    for d in devs:
        print d['name'], '-', d['driver']
        driverClass = d['driver'].split('/')[0].lower()

        # USB serial types -- load appropriate top level driver here.
        try:
            if driverClass == 'tenmaserial':
                from pyLabDataLogger.device import tenmaSerialDevice
                device_list.append(tenmaSerialDevice.tenmaPowerSupplySerialDevice(params=d))
            elif driverClass == 'serial':
                from pyLabDataLogger.device import serialDevice
                device_list.append(serialDevice.serialDevice(params=d))
            elif driverClass == 'arduino':
                from pyLabDataLogger.device import arduinoDevice
                device_list.append(arduinoDevice.arduinoSerialDevice(params=d))
            elif driverClass == 'sigrok':
                from pyLabDataLogger.device import sigrokUsbDevice
                device_list.append(sigrokUsbDevice.srdevice(params=d))
            elif driverClass == 'pyapt':
                from pyLabDataLogger.device import pyAPTDevice
                device_list.append(pyAPTDevice.pyAPTDevice(params=d))
            else:
                print "\tI don't know what to do with this device"
        except KeyError as e: # driver couldn't handle the subdriver settings
            print '\tKeyError:',e
            continue

    return device_list

