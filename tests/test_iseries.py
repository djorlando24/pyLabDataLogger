#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    Omega iSeries Serial Communications Test
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2020 LTRAC
    @license GPL-3.0+
    @version 1.0.1
    @date 19/07/2020
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

import serial
import sys

port = '/dev/ttyUSB0'
baudrate = 9600
bytesize = serial.SEVENBITS
parity = serial.PARITY_ODD
stopbits = serial.STOPBITS_ONE
timeout = 5.

print "Attempt to communicate with Omega iSeries on",port

s = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout)

serialQuery  =   ['*\xb01X\xb01',\
                  '*\xb01R\xb01',\
                  '*\xb01R\xb02',\
                  '*\xb01U\xb01']

#s.open()

for q in serialQuery:
    print "Tx:",repr(q)
    s.write(q+'\r\n')
    sys.stdout.write( "Rx: " )
    c=''; str=''
    while not '\n' in c:    
        c=s.read(1)
        #sys.stdout.write(repr(c))
        sys.stdout.flush()
        str+=c
    print repr(str)
    print ""

print "Close",port
s.close()
