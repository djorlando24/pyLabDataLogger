#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test device support.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 13/06/25

    Multiphase Flow Laboratory
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
import time
from termcolor import cprint

INTERVAL_SECONDS = 0  # set to zero to go as fast as possible

if __name__ == '__main__':

    globalFunctions.banner()
    
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=True)
    
    # kwargs to customise setup of devices
    special_args={'debugMode':True, 'live_preview':True, 'init_tc08_config':['K','K','K','T','T','T','X','X'], 'quiet':False,\
                 'samples':2,\
                 'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2'],\
                  'usbh-rate':3 } 

    if len(usbDevicesFound) == 0: exit()

    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)

    loop_counter = 0
    running_average = 0.
    
    try:
        while True:
            t0 = time.time()
            for d in devices:
                cprint( d.name, 'magenta', attrs=['bold'] )
                d.query()
                d.pprint()
            #time.sleep(.01)
            dt = time.time()-t0
            running_average = ((running_average*float(loop_counter)) + dt)/(float(loop_counter)+1)
            loop_counter += 1
            
            if ((dt<INTERVAL_SECONDS) and (loop_counter>0)): time.sleep(INTERVAL_SECONDS-dt)
            if len(devices)>0: cprint("Polling time = %0.3f sec" % dt, 'cyan')
            
    except KeyboardInterrupt:
        cprint("Stopped.",'red',attrs=['bold'])
        for d in devices: d.deactivate()

    except: # all other errors
        raise

    cprint("Average loop time = %0.3f sec (%i loops, %f Hz max possible)" % (running_average, loop_counter, 1.0/running_average), 'cyan', attrs=['bold'])  