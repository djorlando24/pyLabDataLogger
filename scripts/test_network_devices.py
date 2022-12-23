#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test VISA network device support.
    You need to know the network address of the device, which can usually
    be found on the device's control panel or by pointing a web browser
    to the device's IP Address.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2023 LTRAC
    @license GPL-3.0+
    @version 1.3.0
    @date 23/12/2022
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
from pyLabDataLogger.device.device import pyLabDataLoggerIOError
from pyLabDataLogger.logger import globalFunctions
import time
from termcolor import cprint

if __name__ == '__main__':
    
    globalFunctions.banner()
    
    device_descriptors = [ #{'resource':'TCPIP0::192.168.0.106::5025::SOCKET','driver':'pyvisa/eezbb3'},\
                           {'resource':'TCPIP0::192.168.0.123::INSTR','driver':'pyvisa/dg1000z'},\
                           {'resource':'TCPIP0::192.168.0.124::INSTR','driver':'pyvisa/ds1000z'},\
                           #{'resource':'TCPIP0::192.168.0.125::INSTR','driver':'pyvisa/33220a' },\
    ]

    devices=[]
    for dd in device_descriptors:
        try:
            print('\t',dd)
            devices.append(pyvisaDevice.pyvisaDevice(dd))
        except pyLabDataLoggerIOError:
            pass
    
    if len(devices) == 0: exit()
   
    
    while True:
        for d in devices:
    
            try:
                cprint( d.name, 'magenta', attrs=['bold'] )
                d.query()
                d.pprint()
                d.log('test_log.hdf5')
                
                time.sleep(1)
                print("")
                
            except pyLabDataLoggerIOError:
                pass
                
            except KeyboardInterrupt:
                print("Stopped.")
                break
                
            except: # all other errors
                raise

            
    

    for d in devices:
        print("Disconnecting from %s" % d.name )
        d.deactivate()
        
    exit()
