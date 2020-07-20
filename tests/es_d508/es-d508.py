#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
"""
    Easy Servo Drive ES-D508 RS-232 interface
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2020 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 20/07/2020
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

    Version history:
        20/07/2020 - First version.
"""

'''
    Create byte sequence for a motion command for ES-D508
    based on reverse engineering of signals from test program.
    
    velocity units are revolutions/s
    accel units are revolutions/s^2
    intermission units are milliseconds
'''
import struct
import binascii
#from crccheck.crc import CrcModbus
import libscrc
import numpy as np


def motionCommand(revolutions = 1.0, velocity = 120, accel = 200, intermission = 1000, repeats=1,\
                  current = 100, reverse = False, bidirectional = False, ESD508_ID = '\x01',\
                  pulses_per_rev = 4000, encoder_resolution = 4000, position_err = 1000):
               
    # Commands
    ESD508_WRITE = b'\x06'
    ESD508_READ  = b'\x03'
    
    # Registers
    ESD508_MODE = b'\x09' # RS232 control of motor enabled ??
    ESD508_PREV = b'\x0e' # Motor pulses per revolution [ 0e/0f ? ]
    ESD508_ENCR = b'\x0f' # Encoder resolution per revolution [ 0e/0f ? ]
    ESD508_POSE = b'\x12' # Position error limit
    ESD508_GO   = b'\x14' # command issued before motor begins to move
    ESD508_ACCL = b'\x15' # acceleration
    ESD508_VELO = b'\x16' # velocity
    ESD508_DIST = b'\x18' # distance
    ESD508_NREP = b'\x19' # n repeats
    ESD508_DIRN = b'\x1a' # direction
    ESD508_INTR = b'\x1b' # intermission time
    ESD508_BIDR = b'\x1c' # bidirectional mode
    ESD508_CURR = b'\xd0' # closed loop current %
    ESD508_PULS = b'\x4f' # Pulse mode PUL/DIR [ not sure, not user adjustable? ]
    ESD508_FLTA = b'\x54' # filter enable
    ESD508_FLTR = b'\x55' # filter time
    ESD508_ENAB = b'\x96' # enable active = low
    ESD508_FAUL = b'\x97' # fault active = low
    ESD508_ENQR = b'\xda' # check if data is ready to transfer
    ESD508_TRIG = b'\xff' # rising/falling edges input
    
    # Missing registers:
    # Kp, Ki, Kd, Kvff, HOldCurrent, OpenLoopCurrent, ClosedLoopCurrent?,
    # anti inteference time == intermission time??
    # Pulse Active Edge , Pulse Input Mode ?
    # Current loop autoconfiguration?
    
    # Responses from controller other than echoes of written commands
    ESD508_WAIT = b'\x02\x00\x01' # data not buffered yet
    ESD508_DATA = b'\x02\x00\x02' # buffer ready to send
    
    
    commands = []
    
    # Set up motor parameters.
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_PREV, pulses_per_rev))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_POSE, position_err))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_ENCR, encoder_resolution))
    
    commands.append(struct.pack('>ccxcx?',ESD508_ID, ESD508_WRITE, ESD508_DIRN, reverse))
    commands.append(struct.pack('>ccxcx?',ESD508_ID, ESD508_WRITE, ESD508_BIDR, bidirectional))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_ACCL, accel))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_DIST, revolutions))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_INTR, intermission))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_NREP, repeats))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_VELO, velocity))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_CURR, current))
    
    # not sure what this does, perhaps sets the type of test program to run.
    commands.append(struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, b'\x41', True))
    commands.append(struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, b'\x42', False))
    
    commands.append(struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, ESD508_MODE, True))
    commands.append(struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, ESD508_GO, True))
    
    # add checksums
    setup_commands = []
    for c in commands:
        crc = libscrc.modbus(c)
        setup_commands.append(c + struct.pack('H',crc))
    
    # Now make command set for checking when we expect data to be ready
    enquire_loop  = struct.pack('>ccxcx?',ESD508_ID, ESD508_READ, ESD508_ENQR, True) # ask if ready
    enquire_wait  = struct.pack('>cc3s',ESD508_ID, ESD508_READ, ESD508_WAIT) # not ready
    enquire_ready = struct.pack('>cc3s',ESD508_ID, ESD508_READ, ESD508_DATA) # yes ready
    enquire_send  = struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_GO, 200) # send 200 bytes
    cleanup = struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, ESD508_MODE, False) # end RS232 control program
    
    
    # add checksums
    loop_commands = []
    for c in [ enquire_loop, enquire_wait, enquire_ready, enquire_send, cleanup ]:
        crc = libscrc.modbus(c)
        loop_commands.append( c + struct.pack('H',crc))
    
    return setup_commands, loop_commands
                  

if __name__ == '__main__':

    '''
    print "00c89998 = 200"
    print binascii.hexlify(encodeValue(200))
    print "006499e5 = 100"
    print binascii.hexlify(encodeValue(100))
    '''
    
    for b in motionCommand():
    
        print ""
        if isinstance(b,list):
            for bi in b:
                print binascii.hexlify(bi)
        else:
            print ""
            print binascii.hexlify(b)
