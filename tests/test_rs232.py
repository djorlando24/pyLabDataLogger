#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Testing pins on RS-232 device that pySerial can use.
    
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


import sys
import serial
import time
dt=0.1
if __name__=='__main__':
    if len(sys.argv)<2:
       print("Specify device on command line")
       exit(1)

    s=serial.Serial(sys.argv[1],300) # slow baud for easy analysis
   
    print("\nSending ASCII data on TX")
    try:
       while (True):
        for n in range(256):
           s.write(chr(n))
           time.sleep(dt)
    except KeyboardInterrupt:
       s.write('\n')
    
    print("\nNow loop back TX to RX and find RX. Incoming data will be displayed.")
    try:
       while (True):
        for n in range(256):
           s.write(chr(n))
           time.sleep(dt)
           q=s.read(1)#.strip()
           if len(q)>0:
            sys.stdout.write(repr(q))
            sys.stdout.flush()
    except KeyboardInterrupt:
       print("")
   
    s.close()
    s=serial.Serial(sys.argv[1],dsrdtr=True)
   
    print("Toggling DTR")
    try:
       while (True):
           s.setDTR(1)
           time.sleep(dt)
           s.setDTR(0)
           time.sleep(dt)
    except KeyboardInterrupt:
       s.setDTR(0)

    s.close()
    s=serial.Serial(sys.argv[1],rtscts=True)

    print("\nToggling RTS")
    try:
        while (True):
            s.setRTS(1)
            time.sleep(dt)
            s.setRTS(0)
            time.sleep(dt)
    except KeyboardInterrupt:
        s.setRTS(0)
    
    s.close()
    s=serial.Serial(sys.argv[1],dsrdtr=True)
    
    print("Reading DSR, RI and CD (DTR=Hi out)")
    try:
       s.setDTR(1)
       while (True):
           print("DSR = %s, RI = %s, CD = %s" % (s.getDSR(),s.getRI(),s.getCD()))
           time.sleep(1)
    except KeyboardInterrupt:
       s.setDTR(0)
       

    
       
    print("Done script.")
    s.close()
    
       
       

