#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test device support.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @version 1.0.0
    @date 06/02/2019
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

import time
from termcolor import cprint
from pyLabDataLogger.device import i2cDevice
from pyLabDataLogger.logger import globalFunctions

if __name__ == '__main__':

    globalFunctions.banner()
    
    # I2C setup
    found = i2cDevice.scan_for_devices()
    if len(found)==0: 
        cprint( "No I2C devices found.", 'red',attrs=['bold'])
    else:
        devices = i2cDevice.load_i2c_devices(found)
       
    try:
        while True:
            for d in devices:
                cprint( d.name, 'magenta', attrs=['bold'] )
                d.query()
                d.pprint()
            time.sleep(1)
            print("")
    except KeyboardInterrupt:
        cprint( "Stopped.", 'red',attrs=['bold'])
    except: # all other errors
        raise
     

