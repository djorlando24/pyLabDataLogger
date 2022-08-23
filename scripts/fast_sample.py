#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Fast-as-possible sampling and write to ASCII.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2
    @date 23/08/2022
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
import time, datetime
import numpy as np
from termcolor import cprint

if __name__ == '__main__':

    display_interval = 15

    globalFunctions.banner()

    usbDevicesFound = usbDevice.search_for_usb_devices()
    
    # kwargs to customise setup of devices
    special_args={} 

    if len(usbDevicesFound) == 0: exit()

    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)
   
    t = []
    values = {}
    for d in devices: values[d.name]=[]
    loop_counter = 0
    running_average = 0.
    logfilename='logfile_%s.txt' %  datetime.datetime.now().strftime('%d-%m-%y_%Hh%Mm%Ss')
    t_start_program = time.time()
    try:
        while True:
            t0 = time.time() - t_start_program
            t.append(t0)
            for d in devices:
                # read values
                d.query()
                # show values?
                if loop_counter%display_interval == 0:
                    cprint( d.name, 'magenta', attrs=['bold'] )
                    d.pprint()
                # save data
                values[d.name].append(d.lastValue)
                
            dt = time.time()-t0- t_start_program
            running_average = ((running_average*float(loop_counter)) + dt)/(float(loop_counter)+1)
            loop_counter += 1
            if loop_counter%display_interval == 0: cprint("Polling time = %0.3f sec per read" % dt, 'cyan')
            
    except KeyboardInterrupt:
        cprint("Stopped.",'red',attrs=['bold'])
        for d in devices: d.deactivate()
        
    except: # all other errors
        raise
        
    cprint("Average loop time = %0.3f sec (%i loops)" % (running_average, loop_counter), 'cyan', attrs=['bold'])
    
    # Save file
    with open(logfilename,'w') as F:
        F.write("#TimeSinceProgStart(s)\t%s\n" % '\t'.join(values.keys()))
        
        for i in range(len(t)):
            F.write('%f' % t[i])
            for d in values.keys():
                if len(values[d])<(i+1): F.write('\t')
                else: 
                    if (len(values[d][i])==1): F.write('\t%g' % values[d][i][0])
                    else: F.write('\t%s' % values[d][i])
            F.write('\n')
            
    cprint("Wrote %s." % logfilename,'white')
    exit()
