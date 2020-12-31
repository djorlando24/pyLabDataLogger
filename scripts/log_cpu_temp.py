#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Log lm-sensors data (CPU temps etc) and any USB devices every few minutes.
    
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

from pyLabDataLogger.device import usbDevice
from pyLabDataLogger.device import lmsensorsDevice
from pyLabDataLogger.logger import globalFunctions
import time
from termcolor import cprint

INTERVAL_SECONDS=60

if __name__ == '__main__':
    globalFunctions.banner()
    
    logfilename='log_%s.hdf5' % (time.strftime("%Y-%m-%d-%H-%M-%S"))

    # AUTO-LOAD ANY USB DEVICE
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    special_args={} # default/init settings
    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)
    
    # HERE WE MANUALLY LOAD lmsensors DEVICE
    devices.append(lmsensorsDevice.lmsensorsDevice())

    if len(devices) == 0: exit()
   
    try:
        while True:
            for d in devices:
                cprint( d.name, 'magenta', attrs=['bold'])
                d.query()
                d.pprint()
                d.log(logfilename)
            time.sleep(INTERVAL_SECONDS)
            print("")
    except KeyboardInterrupt:
        cprint("\nStopped.",red,attrs=['bold'])
    except: # all other errors
        raise
