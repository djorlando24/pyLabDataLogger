#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test device support.
    
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

from pyLabDataLogger.device import usbDevice

if __name__ == '__main__':
    
    #usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=True)
    #print len(usbDevicesFound),'recognised devices found'
    
    devices = usbDevice.load_usb_devices()#usbDevicesFound)
    
    '''
    from sigrokUsbDevice import srdevice
    from serialDevice import *
    from tenmaSerialDevice import *
    for usbDeviceEntry in usbDevicesFound:
        if usbDeviceEntry['driver'].split('/')[0] == 'sigrok':
            dev = srdevice(usbDeviceEntry)
        elif usbDeviceEntry['driver'] == 'serial/arduino':
            #usbDeviceEntry['port']='/dev/tty.usbmodem331571'  # TESTING
            dev = arduinoSerialDevice(usbDeviceEntry)
        elif usbDeviceEntry['driver'] == 'serial/tenma722710':
            #usbDeviceEntry['port']='/dev/tty.usbmodem1411'    # TESTING
            dev = tenmaPowerSupplySerialDevice(usbDeviceEntry)
    '''

