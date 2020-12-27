#!/usr/bin/env python3
"""
    DataQ Serial Device checker - determine serial port parameters by brute force.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @version 1.1.0
    @date 27/12/2020
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    Note on implementation of serial commands: 
     - commas denote a sequence of commands sent as quickly as possible.
     - a double-comma denotes a pause for data aquisition by the client device,
       where the delay is set by params['sample_period'].
    
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

import serial, sys

if __name__  == '__main__':
    

    if len(sys.argv)<2: 
        print("Usage: specify TTY on command line")
        exit(1)

    cmd = '\x00A\x00'
    #cmd='info 0'

    for xonxoff, rtscts in [(False,False),(True,False),(False,True)]:
        for termchr in ['\r','\n','\r\n']:
            for baudrate in [4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]:
                for bytesize in [serial.EIGHTBITS, serial.SEVENBITS ]:
                    for parity in [serial.PARITY_NONE, serial.PARITY_ODD, serial.PARITY_EVEN]:
                        for stopbits in [serial.STOPBITS_ONE, serial.STOPBITS_TWO]:
                    
                            fcmd = (cmd+termchr).encode('ascii')
                            sys.stdout.write('%06i %s %s %s soft:%i hard:%i cmd=%s: ' % (baudrate,bytesize,parity,stopbits,xonxoff,rtscts,repr(fcmd)))
                            sys.stdout.flush()
                            
                            S = serial.Serial(port=sys.argv[1], baudrate=baudrate, bytesize=bytesize, parity=parity,\
                                              stopbits=stopbits, xonxoff=xonxoff, rtscts=rtscts, timeout=.1, write_timeout=.1)

                            S.write(fcmd)
                            ret = S.read(32).decode('ascii')
                            print('\t',ret)
                            sys.stdout.flush()
                            if len(ret)>0: exit()
                            S.close()

    exit()
