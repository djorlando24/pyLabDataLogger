#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test device support - log to file
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2020 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 19/07/2020
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from pyLabDataLogger.device import usbDevice
import datetime,time
from termcolor import cprint

if __name__ == '__main__':
    
    logfilename='logfile_%s.hdf5' %  datetime.datetime.now().strftime('%d-%m-%y_%Hh%Mm%Ss')
    
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    
    # kwargs to customise setup of devices
    special_args={'live_preview':True, 'debugMode':True, 'init_tc08_config':['K','K','K','T','T','T','X','X'], 'quiet':False,\
                  'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}

    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)

    if len(devices) == 0: exit()
    loop_counter = 0
    running_average = 0.
    try:
        while True:
            t0 = time.time()
            for d in devices:
                print('\n'+d.name)
                d.query()
                d.pprint()
                d.log(logfilename)
            #time.sleep(0.01)
            dt = time.time()-t0
            running_average = ((running_average*float(loop_counter)) + dt)/(float(loop_counter)+1)
            loop_counter += 1
            cprint("Loop time = %0.3f sec" % dt, 'cyan')
            
    except KeyboardInterrupt:
        cprint( "Stopped.", 'red', attrs=['bold'])
        
    except: # all other errors
        raise

    cprint("Average loop time = %0.3f sec (%i loops)" % (running_average, loop_counter), 'cyan', attrs=['bold'])    
