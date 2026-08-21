#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test HTTPS API [network] device support.
    You need to know the URL of the device, which can usually
    be provided by the manufacturer's web dashboard or on the 
    device itself. There's usually a secret key in the URL.
    
    Put a list of URLs in the file webAPIkeys.txt .   
        This file can have comments starting with '#'.
        Each line can be a URL or `URL<tab>Name` or `URL<tab>Name<tab>Format`.
 
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

from pyLabDataLogger.device import webAPIDevice
from pyLabDataLogger.device.device import pyLabDataLoggerIOError
from pyLabDataLogger.logger import globalFunctions
import time
from termcolor import cprint

if __name__ == '__main__':
    
    globalFunctions.banner()
    
    devices=[]
    with open("webAPIkeys.txt",'r') as F:
        for l in F.readlines():
            if len(l)>0:
                if l[0] != '#':
                    try:
                        apilist = l.strip().split()
                        url=apilist[0]
                        name=None; fmt='json'
                        if len(apilist)>1: 
                           name=apilist[1]
                           cprint('%s - %s' % (name,url),'cyan',attrs=['bold'])
                           if len(apilist)>2: fmt=apilist[2] 
                        else:
                           cprint(url, 'cyan', attrs=['bold'])
                        devices.append(webAPIDevice.webAPIDevice(url=url,name=name,format=fmt))
                    except pyLabDataLoggerIOError:
                        pass
    
    if len(devices) == 0: exit()
    
    while True:
        for d in devices:
    
            try:
                cprint( d.name, 'magenta', attrs=['bold'] )
                d.query()
                d.pprint()
                d.log('test_log.hdf5')
                
                time.sleep(1)
                print("")
                
            except pyLabDataLoggerIOError:
                pass
                
            except KeyboardInterrupt:
                print("Stopped.")
                for d in devices: d.deactivate()
                exit(0) 
                
            except: # all other errors
                raise
