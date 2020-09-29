#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test raspberry pi device support:
        - hardware UART talking to a serial device
        - GPIO pins
        - I2C devices
        - SPI devices
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @version 1.0.2
    @date 28/11/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from pyLabDataLogger.device import usbDevice, serialDevice, i2cDevice, gpioDevice
import time, serial

if __name__ == '__main__':

    devices=[]

    # kwargs to customise setup of devices
    special_args={'debugMode':True, 'init_tc08_config':['K','K','K','T','T','T','X','X'],\
                  'quiet':False, 'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}

    """
    # Serial via UART setup
    d={'driver':'serial/omega-iseries', 'name':'Omega iSeries via RPi UART', 'port':'/dev/serial0'}
    devices.append(serialDevice.serialDevice(params=d,**special_args))
    """

    # GPIO pins setup
    gpioInputPins=(5,6,19,20,16,17,18)
    gpioInputPullup=(False,False,True,True,True,True,True) # pull up inputs
    gpioChannelNames=['TTLIn1','TTLIn2','HX Water low','Heating','But1','But2','But3']
    devices.append(gpioDevice.gpioDevice({'pins':gpioInputPins,'pup':gpioInputPullup,'channel_names':gpioChannelNames}))

    # I2C setup    
    found = i2cDevice.scan_for_devices()
    if len(found)==0: 
        print "No I2C devices found."
    else:
        devices.extend(i2cDevice.load_i2c_devices(found, **special_args)) 
    
    
    # USB setup
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=special_args['debugMode'])
    devices.extend(usbDevice.load_usb_devices(usbDevicesFound, **special_args))
    
    
    # Reporting loop
    try:
        while True:
            for d in devices:
                print d.name
                d.query()
                d.pprint()
            time.sleep(1)
    except KeyboardInterrupt:
        print "Stopped."
    except:
        raise
     

