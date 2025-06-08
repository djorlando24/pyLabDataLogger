#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Log lm-sensors data (CPU temps etc) and any USB devices every few minutes.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2023 LTRAC
    @license GPL-3.0+
    @version 1.4.0
    @date 08/06/25

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
from pyLabDataLogger.device import lmsensorsDevice
from pyLabDataLogger.logger import globalFunctions
import time
from termcolor import cprint

INTERVAL_SECONDS=10.0

if __name__ == '__main__':
    globalFunctions.banner()
    
    logfilename='log_%s.hdf5' % (time.strftime("%Y-%m-%d-%H-%M-%S"))

    # AUTO-LOAD ANY USB DEVICE
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    special_args={'live_preview':True, 'debugMode':False, 'quiet':True} # default/init settings
    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)
    
    # HERE WE MANUALLY LOAD lmsensors DEVICE
    devices.append(lmsensorsDevice.lmsensorsDevice(**special_args))

    if len(devices) == 0: exit()
    loop_counter = 0
    running_average = 0.
    try:
        while True:
            t0 = time.time()
            for d in devices:
                cprint('\n'+d.name, 'magenta', attrs=['bold'])
                d.query()
                d.pprint()
                d.log(logfilename)
            
            dt = time.time()-t0
            running_average = ((running_average*float(loop_counter)) + dt)/(float(loop_counter)+1)
            loop_counter += 1
            
            if ((dt<INTERVAL_SECONDS) and (loop_counter>0)): time.sleep(INTERVAL_SECONDS-dt)
            cprint("Polling time = %0.3f sec" % dt, 'cyan')
            
    except KeyboardInterrupt:
        cprint("\nStopped.",'red',attrs=['bold'])
        for d in devices: d.deactivate()
    except: # all other errors
        raise
        
    cprint("Average loop time = %0.3f sec (%i loops)" % (running_average, loop_counter), 'cyan', attrs=['bold'])    
