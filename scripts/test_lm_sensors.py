#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test lm-sensors support.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.0
    @date 20/12/2020
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from pyLabDataLogger.device import lmsensorsDevice
from pyLabDataLogger.logger import globalFunctions
import time

if __name__ == '__main__':
    
    globalFunctions.banner()
    
    devices = [lmsensorsDevice.lmsensorsDevice(quiet=False)]

    if len(devices) == 0: exit()
   
    try:
        while True:
            for d in devices:
                cprint( d.name, 'magenta', attrs=['bold'] )
                d.query()
                d.pprint()
                d.log('lm_sensors_test_log.hdf5')
            time.sleep(1)
            print("")
    except KeyboardInterrupt:
        print "Stopped."
    except: # all other errors
        raise
