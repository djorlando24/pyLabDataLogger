#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Log USB devices to file each time ENTER is pressed.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @version 1.0.2
    @date 18/07/2020
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
from pyLabDataLogger.logger import globalFunctions
import datetime, time
import Tkinter as tk
import tkMessageBox as mb
from termcolor import cprint

if __name__ == '__main__':
    globalFunctions.banner()
    
    logfilename='logfile_%s.hdf5' %  datetime.datetime.now().strftime('%d-%m-%y_%Hh%Mm%Ss')
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    
    # kwargs to customise setup of devices
    special_args={'live_preview':True, 'debugMode':True, 'init_tc08_config':['K','K','K','T','T','T','X','X'], 'quiet':False,\
                  'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}

    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)

    if len(devices) == 0: exit()
   
    try:
        while True:
            for d in devices:
                cprint( d.name, 'magenta', attrs=['bold'])
                d.query()
                d.pprint()
                d.log(logfilename)
            time.sleep(1)
            if not mb.askokcancel('pyLabDataLogger','Press OK to take next data or CANCEL to exit'): 
            	cprint( "Stopped.", 'red', attrs=['bold'])
            	exit()
    except KeyboardInterrupt:
        cprint( "Stopped.", 'red', attrs=['bold'])
    except: # all other errors
        raise
