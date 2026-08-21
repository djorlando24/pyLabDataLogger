#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test libcamera support - log to file
    
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

from pyLabDataLogger.device import usbDevice, libcameraDevice
from pyLabDataLogger.logger import globalFunctions
import datetime,time
from termcolor import cprint

if __name__ == '__main__':
    
    globalFunctions.banner()
    
    logfilename='logfile_%s.hdf5' %  datetime.datetime.now().strftime('%d-%m-%y_%Hh%Mm%Ss')
    
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    
    # kwargs to customise setup of devices
    special_args={'live_preview':True, 'debugMode':False, 'quiet':False, 'revolutions':1.0,\
                  'init_tc08_config':['K','K','K','T','T','T','X','X'], \
                  'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}

    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)

    # Here load CSI camera. I used the Raspi HQ Camera's resolution as my setting.
    # This requires 256MB of GPU shared memory space.
    devices.append(libcameraDevice.libcameraDevice(resolution=(4056,3040),live_preview=True,quiet=False))

    if len(devices) == 0: exit()
    loop_counter = 0
    running_average = 0.
    try:
        while True:
            t0 = time.time()
            for d in devices:
                cprint('\n'+d.name,'magenta',attrs=['bold'])
                d.query()
                d.pprint()
                d.log(logfilename)
            
            #time.sleep(0.01) # optional slowdown
            
            dt = time.time()-t0
            running_average = ((running_average*float(loop_counter)) + dt)/(float(loop_counter)+1)
            loop_counter += 1
            cprint("Loop time = %0.3f sec" % dt, 'cyan')
            
    except KeyboardInterrupt:
        cprint( "Stopped.", 'red', attrs=['bold'])
        for d in devices: d.deactivate()
        
    except: # all other errors
        raise

    cprint("Average loop time = %0.3f sec (%i loops)" % (running_average, loop_counter), 'cyan', attrs=['bold'])    
