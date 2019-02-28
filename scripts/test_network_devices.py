#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test VISA network device support.
    You need to know the network address of the device, which can usually
    be found on the device's control panel or by pointing a web browser
    to the device's IP Address.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 28/02/2019
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from pyLabDataLogger.device import pyvisaDevice
import time

if __name__ == '__main__':
    
    devices = [pyvisaDevice.pyvisaDevice({'resource':'TCPIP0::192.168.0.123::INSTR','driver':'pyvisa/dg1000z'}),\
               pyvisaDevice.pyvisaDevice({'resource':'TCPIP0::192.168.0.124::INSTR','driver':'pyvisa/ds1000z'})]

    if len(devices) == 0: exit()
   
    try:
        while True:
            for d in devices:
                print '-'*79
                print d.name
                d.query()
                d.pprint()
            time.sleep(1)
    except KeyboardInterrupt:
        print "Stopped."
    except: # all other errors
        raise
