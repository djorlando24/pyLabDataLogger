#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test VISA network device support.
    You need to know the network address of the device, which can usually
    be found on the device's control panel or by pointing a web browser
    to the device's IP Address.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @version 1.0.0
    @date 28/02/2019
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from pyLabDataLogger.device import pyvisaDevice
from pyLabDataLogger.logger import globalFunctions
import time
from termcolor import cprint

if __name__ == '__main__':
    
    globalFunctions.banner()
    
    devices = [pyvisaDevice.pyvisaDevice({'resource':'TCPIP0::192.168.0.123::INSTR','driver':'pyvisa/dg1000z'}),\
               pyvisaDevice.pyvisaDevice({'resource':'TCPIP0::192.168.0.124::INSTR','driver':'pyvisa/ds1000z'}),\
               pyvisaDevice.pyvisaDevice({'resource':'TCPIP0::192.168.0.125::INSTR','driver':'pyvisa/33220a' })]

    if len(devices) == 0: exit()
   
    try:
        while True:
            for d in devices:
                cprint( d.name, 'magenta', attrs=['bold'] )
                d.query()
                d.pprint()
                d.log('test_log.hdf5')
            time.sleep(1)
            print("")
    except KeyboardInterrupt:
        print "Stopped."
    except: # all other errors
        raise
