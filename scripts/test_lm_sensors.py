#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test lm-sensors support.
    
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
        for d in devices: d.deactivate()

    except: # all other errors
        raise
