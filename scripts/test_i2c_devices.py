#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test device support.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 06/02/2019
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

import time

if __name__ == '__main__':

    # I2C setup    
    from pyLabDataLogger.device import i2cDevice
    found = i2cDevice.scan_for_devices()
    if len(found)==0: 
        print "No I2C devices found."
    else:
        devices = i2cDevice.load_i2c_devices(found)
       
    try:
        while True:
            time.sleep(1)
            for d in devices:
                print d.name
                d.query()
                d.pprint()
    except KeyboardInterrupt:
        print "Stopped."
    except: # all other errors
        raise
     

