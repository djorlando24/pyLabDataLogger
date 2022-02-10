#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test device support - log to file
    Each device runs in its own thread.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2
    @date 19/01/2022
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

from pyLabDataLogger.device import usbDevice, i2cDevice
from pyLabDataLogger.logger import globalFunctions
from termcolor import cprint
import time

if __name__ == '__main__':
    
    globalFunctions.banner()
    logfilename='test_log.hdf5'

    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    i2cDevicesFound = i2cDevice.scan_for_devices()
    
    # kwargs to customise setup of devices
    special_args={'debugMode':True, 'init_tc08_config':['K','K','K','T','T','T','X','X'], 'quiet':False, 'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}

    # BELOW IS THE CURRENT SERIALIZED CODE!
    
    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)
    devices.extend( i2cDevice.load_i2c_devices(found) )
    
    if len(devices) == 0: exit()
   
    try:
        while True:
            for d in devices:
                cprint( d.name, 'magenta', attrs=['bold'])
                d.query()
                d.pprint()
                d.log(logfilename)
            time.sleep(1)
            print("")
    except KeyboardInterrupt:
        cprint( "Stopped.",'red',attrs=['bold'])
        for d in devices: d.deactivate()
    except: # all other errors
        raise
