#!/usr/bin/env python3
"""
    Test I2C device via i2cmini adapter
    
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

import sys
import i2cdriver
from termcolor import cprint

if __name__=='__main__':

    if len(sys.argv)<2: ttys=["/dev/ttyUSB1"]
    else: ttys=sys.argv[1:]
    
    for tty in ttys:
        cprint("Connecting to i2cmini on %s" % tty, 'cyan')
        i2c = i2cdriver.I2CDriver(tty)
        cprint("Scanning for devices",'white')
        i2c.scan()
        
