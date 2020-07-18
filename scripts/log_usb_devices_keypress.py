#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Log USB devices to file each time ENTER is pressed.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 09/07/2020
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from pyLabDataLogger.device import usbDevice
import datetime

if __name__ == '__main__':
    
    logfilename='logfile_%s.hdf5' %  datetime.datetime.now().strftime('%d-%m-%y_%Hh%Mm%Ss')
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    
    # kwargs to customise setup of devices
    special_args={'live_preview':True, 'debugMode':False, 'init_tc08_config':['K','K','K','T','T','T','X','X'], 'quiet':False, 'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}

    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)

    if len(devices) == 0: exit()
   
    try:
        while True:
            for d in devices:
                print d.name
                d.query()
                d.pprint()
                d.log(logfilename)
            key=raw_input("Press ENTER to continue or CTRL-C to exit")
    except KeyboardInterrupt:
        print "Stopped."
    except: # all other errors
        raise
