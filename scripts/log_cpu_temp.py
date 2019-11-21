#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Log lm-sensors data (CPU temps etc) and any USB devices every few minutes.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 21/11/2019
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from pyLabDataLogger.device import usbDevice
from pyLabDataLogger.device import lmsensorsDevice
import time

INTERVAL_SECONDS=60

if __name__ == '__main__':
    
    logfilename='log_%i.hdf5' % (ddmmyy)

    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    
    # kwargs to customise setup of devices
    #special_args={'debugMode':True, 'init_tc08_config':['K','K','K','T','T','T','X','X'], 'quiet':False, 'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}

    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)
    devices.append(lmsensorsDevice.lmsensorsDevice())

    if len(devices) == 0: exit()
   
    try:
        while True:
            for d in devices:
                print d.name
                d.query()
                d.pprint()
                d.log(logfilename)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print "Stopped."
    except: # all other errors
        raise
