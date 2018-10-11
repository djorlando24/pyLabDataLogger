#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    master USB device support for pyLabDataLogger
    
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

# Known hardware.
usb_device_table = [
    {'vid':0x1a86, 'pid':0xe008, 'bcdDevice':0x1300, 'driver':'sigrok/uni-t-ut32x', 'name':'Tenma 72-7712 Thermometer'},\
    {'vid':0x1a86, 'pid':0xe008, 'bcdDevice':0x1400, 'driver':'sigrok/tenma-72-7730', 'name':'Tenma 72-7730A Multimeter'},\
    {'vid':0x1ab1, 'pid':0x04ce, 'driver':'sigrok/rigol-ds', 'name':'Rigol DS Oscilloscope'},\
    {'vid':0x08a9, 'pid':0x0014, 'driver':'sigrok/fx2lafw', 'name':'LHT00SU1 logic analyzer'},\
                    
    {'vid':0x1b3f, 'pid':0x2008, 'driver':'alsa', 'name':'USB sound card'},\
    {'vid':0x0403, 'pid':0xfaf0, 'driver':'pyapt', 'name':'Thorlabs APT motor driver'},\
    {'vid':0x0136, 'pid':0x0112, 'driver':'mcc-libusb/usb-1608g', 'name':'MCC USB-1608GX-2AO ADC'},\
                    
    {'vid':0x0416, 'pid':0x5011, 'driver':'serial/tenma722710', 'name':'Tenma 72-2710 Power Supply'},\
    {'vid':0x0557, 'pid':0x2008, 'driver':'serial/ohaus7k', 'name':'OHAUS Valor 7000 scale (RS232)'},\

    {'vid':0x0525, 'pid':0xa4aa, 'driver':'serial/shell', 'name':'C.H.I.P. (CDC composite gadget)'},\
    {'vid':0x10c4, 'pid':0xea60, 'driver':'serial/shell', 'serial':'0001', 'name':'Onion Omega2+'},\
    {'vid':0x1d6b, 'pid':0x0104, 'driver':'serial/shell', 'name':'Beaglebone Black'},\
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/shell', 'bcdDevice':0x600, 'name':'Intel Edison A502OTFN'},\
    
    #{'vid':0x0403, 'pid':0x6001, 'driver':'serial/omega-process-controller', 'name':'FTDI USB to RS485 adapter'},\
    
    {'vid':0x0403, 'pid':0x6015, 'serial':'DB00VHJZ', 'driver':'serial/gpib', 'name':'GPIB-USB adapter'},\
    
    {'vid':0x067b, 'pid':0x2303, 'driver':'serial/arduino', 'name':'Generic USB to serial cable'},\
    {'vid':0x1a86, 'pid':0x7523, 'driver':'serial/arduino', 'name':'Generic USB to serial cable'},\
    {'vid':0x0403, 'pid':0x6001, 'driver':'serial/arduino', 'name':'FTDI USB to Serial'},\
    {'vid':0x0403, 'pid':0x6015, 'driver':'serial/arduino', 'name':'FTDI USB to Serial'},\
    {'vid':0x10c4, 'pid':0xea60, 'driver':'serial/arduino', 'name':'CP2102 USB to Serial'},\
    
    {'vid':0x2341, 'pid':0x8036, 'driver':'serial/arduino', 'name':'uDuino (Leonardo)'},
    {'vid':0x16c0, 'pid':0x0483, 'driver':'serial/arduino', 'name':'Teensy microcontroller'},\
    {'vid':0x04b4, 'pid':0x0006, 'driver':'serial/arduino', 'name':'Cypress CY7C65213 USB to Serial'},\
    {'vid':0x04b4, 'pid':0xf139, 'driver':'serial/arduino', 'name':'Cypress PSoC5LP'},\
    {'vid':0x2341, 'pid':0x0043, 'driver':'serial/arduino', 'name':'Arduino Uno'},\
    {'vid':0x2b04, 'pid':0xc006, 'driver':'serial/arduino', 'name':'Particle Photon'},\
]

#{'vid':0x0000, 'pid':0x0000, 'driver':'usbtc08', 'name':'Picolog USB TC-08 thermocouple datalogger'},\

# Search table for a match
def match_device(dev):
    for match in usb_device_table:
        # Find matching VID and PID
        if (dev.idVendor == match['vid']) and (dev.idProduct == match['pid']):
            matching=True
            # Match bcdDevice and serial if necessary
            if 'bcdDevice' in match.keys():
                if match['bcdDevice'] != dev.bcdDevice: matching=False
                elif match['bcdDevice'] is None: matching=True
            if 'serial' in match.keys():
                if match['serial'] != dev.serial_number: matching=False
                elif match['serial'] is None: matching=True
            if matching: return match
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
        if debugMode: print 'bus=%03i address=%03i : vid=0x%04x pid=0x%04x : class=0x%02x device=0x%04x serial=%s' % (dev.bus, dev.address, dev.idVendor, dev.idProduct,dev.bDeviceClass,dev.bcdDevice,dev.serial_number)
        table_entry = match_device(dev)
        if table_entry is not None:
            print '- found %s, driver=%s' % (table_entry['name'],table_entry['driver'])
            found_entries.append(table_entry)

    return found_entries
