#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test device support - display using Matplotlib
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2 BETA
    @date 11/12/2021
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
import datetime,time
import numpy as np
import matplotlib.pyplot as plt
from termcolor import cprint

if __name__ == '__main__':
    
    globalFunctions.banner()
    
    logfilename='logfile_%s.hdf5' %  datetime.datetime.now().strftime('%d-%m-%y_%Hh%Mm%Ss')
    
    usbDevicesFound = usbDevice.search_for_usb_devices(debugMode=False)
    
    # kwargs to customise setup of devices
    special_args={'live_preview':True, 'debugMode':False, 'quiet':True, 'revolutions':1.0,\
                  'init_tc08_config':['K','K','K','T','T','T','X','X'], \
                  'init_tc08_chnames':['Cold Junction','K1','K2','K3','T4','T5','T6','420mA_P1','420mA_P2']}

    devices = usbDevice.load_usb_devices(usbDevicesFound, **special_args)
    
    from pyLabDataLogger.device import dummyDevice
    
    # Create some fake devices to fill the plot up with stuff. TESTING ONLY
    devices.append(dummyDevice.dummyDevice(params={'period':10.}, **special_args))
    
    devices.append(dummyDevice.dummyDevice(params={'period':10., 'n_channels':2}, **special_args))
    
    devices[-1].name='Dummy2'
    devices[-1].config['eng_units'][0] = 'V'
    devices[-1].config['scale'][0]=2.0

    if len(devices) == 0: exit()
    
    SAMPLE_PERIOD=0.25 # will attempt to hit this, it is just a *minimum*.
    
    # Setup figure
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.grid(alpha=.33)
    plt.title("pyLabDataLogger")
    plt.xlabel("Time [s]")
    sampledTimes=[0.]
    
    # Set which channels to plot (default 1 per device for testing)
    for d in devices:
        d.plotCh=0
        d.history=[np.nan]
        d.plotHandle,=ax.plot(sampledTimes,d.history,marker='o',lw=1,label='%s %s [%s]' % (d.name,d.config['channel_names'][d.plotCh],d.config['eng_units'][d.plotCh]))
    plt.legend(loc=1)
    plt.ion()
    plt.draw()
    plt.pause(0.01)
    yrange=[-1e-12,1e-12]
    
    loop_counter = 0
    running_average = 0.
    loop_starting_time = time.time()
    try:
        while True:
            t0 = time.time()
            sampledTimes.append(t0-loop_starting_time)
            for d in devices:
                cprint('\n'+d.name,'magenta',attrs=['bold'])
                d.query()
                d.pprint()
                d.log(logfilename)
                
                d.history.append(d.lastScaled[d.plotCh])
                d.plotHandle.set_xdata(sampledTimes)
                d.plotHandle.set_ydata(d.history)
                if np.nanmin(d.history)<yrange[0]: yrange[0]=np.nanmin(d.history)
                if np.nanmax(d.history)>yrange[1]: yrange[1]=np.nanmax(d.history)
                ax.set_xlim(np.min(sampledTimes),np.max(sampledTimes))
                ax.set_ylim(*yrange)
                plt.draw()
                plt.pause(0.01)
                
            
            while ((time.time()-t0)<SAMPLE_PERIOD):
                time.sleep(0.01)
            
            dt = time.time()-t0
            running_average = ((running_average*float(loop_counter)) + dt)/(float(loop_counter)+1)
            
            loop_counter += 1
            if (loop_counter%10 == 0):
                cprint("Loop time = %0.3f sec" % dt, 'cyan')
            
    except KeyboardInterrupt:
        cprint( "Stopped.", 'red', attrs=['bold'])
        
    except: # all other errors
        raise

    cprint("Average loop time = %0.3f sec (%i loops)" % (running_average, loop_counter), 'cyan', attrs=['bold'])    
