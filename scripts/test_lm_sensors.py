#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test lm-sensors support.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 20/11/2019
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from pyLabDataLogger.device import lmsensorsDevice
import time

if __name__ == '__main__':
    
    devices = [lmsensorsDevice.lmsensorsDevice()]

    if len(devices) == 0: exit()
   
    try:
        while True:
            for d in devices:
                print '-'*79
                print d.name
                d.query()
                d.pprint()
                #d.log('test_log.hdf5')
            time.sleep(2)
    except KeyboardInterrupt:
        print "Stopped."
    except: # all other errors
        raise
