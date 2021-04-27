#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Newport P6000A frequency counter Serial Communications Test
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.3
    @date 06/04/2021
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
import time

port = '/dev/ttyUSB0'
baudrate = 9600		
bytesize = serial.SEVENBITS
parity = serial.PARITY_EVEN
stopbits = serial.STOPBITS_ONE	
timeout = 10.

print( "Attempt to communicate with P6000A on",port)	

s = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout, rtscts=False)
s.rts=False
s.dtr=False

serialQuery  =   [b'@U?G\r']


for q in serialQuery:
    print("Tx:",repr(q))
    s.rts=False
    s.dtr=False
    time.sleep(0.010)
    s.write(q	)
    sys.stdout.write( "Rx: " )
    c=b''; respstr=b''
    time.sleep(0.050)
    s.rts=True
    s.dtr=True
    time.sleep(0.015)
    while not b'\r' in c:    
        c=s.read(1)
        sys.stdout.write(c.decode('ascii'))
        sys.stdout.flush()
        respstr+=c
    #print(repr(respstr))	
    print("")

print("Try read normal value: ")
time.sleep(.5)
s.rts=True
s.dtr=True
time.sleep(0.05)
for n in range(255):
    sys.stdout.write(repr(s.read(12)))
    sys.stdout.flush()
s.rts=False
s.dtr=False

print("Close",port)
s.close()
