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
    
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    
    # kwargs to customise setup of devices
    special_args={'debugMode':False, 'init_tc_config':['K','K','K','T','T','T','X','X'], 'quiet':False,
                  'init_ch_names':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2'], 'nothingparam':None}

    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)
    

