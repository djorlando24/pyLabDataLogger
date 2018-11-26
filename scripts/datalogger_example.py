#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Example script of data logging with custom device setup.   
 
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 27/11/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from pyLabDataLogger.device import usbDevice
from pyLabDataLogger.logger import multiThreadedLogger
import time

if __name__ == '__main__':
   
    # step 1 - identify our hardware. 
    # autodetect any USB devices.
    devices = usbDevice.search_for_usb_devices(debugMode=False)
    
    # now manually define some other device. 

    # kwargs to customise setup of devices - these parameters aren't autodetected and will be ignored by devices they don't pertain to.
    special_args={'debugMode':True, 'init_tc08_config':['K','K','K','T','T','T','X','X'], 'quiet':False, 'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}

    # Now spawn a thread for each device and start the logger.
    sample_rate = 2.0 # seconds wait average between logging.
    multiThreadedLogger.start("test.hdf5", sample_rate, devices, **special_args)
