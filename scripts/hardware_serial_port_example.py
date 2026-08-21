#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test device support - log to file
    
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

from pyLabDataLogger.logger import globalFunctions
from pyLabDataLogger.device import serialDevice
import datetime,time
from termcolor import cprint

INTERVAL_SECONDS = 0.5  # set to zero to go as fast as possible

if __name__ == '__main__':
    
    globalFunctions.banner()
    
    logfilename='logfile_%s.hdf5' %  datetime.datetime.now().strftime('%d-%m-%y_%Hh%Mm%Ss')
    
    # kwargs to customise setup of some specific devices
    special_args={'ID':'A'}
    
    # Load a serial device with a specified driver at a specified tty
    devices.append(serialDevice.serialDevice({'quiet':True, 'debugMode':False, 'name':'hardwareSerial',\
                                              'tty':'/dev/ttyS0', 'driver':'serial/...'},**special_args)

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
            
            dt = time.time()-t0
            running_average = ((running_average*float(loop_counter)) + dt)/(float(loop_counter)+1)
            loop_counter += 1
            
            if ((dt<INTERVAL_SECONDS) and (loop_counter>0)): time.sleep(INTERVAL_SECONDS-dt)
            cprint("Polling time = %0.3f sec" % dt, 'cyan')
            
    except KeyboardInterrupt:
        cprint( "Stopped.", 'red', attrs=['bold'])
        for d in devices: d.deactivate()
        
    except: # all other errors
        raise

    cprint("Average loop time = %0.3f sec (%i loops, %f Hz max possible)" % (running_average, loop_counter, 1.0/running_average), 'cyan', attrs=['bold'])    
