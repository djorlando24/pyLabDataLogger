#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Easy Servo Drive ES-D508 RS-232 functions.
    This is not a pyLabDataLogger class, just a bunch of functions we can call
    to do useful things. serialDevice will handle the low level communication.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2023 LTRAC
    @license GPL-3.0+
    @version 1.3.0
    @date 23/12/2022
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
        30/07/2020 - First version.
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
import libscrc
import numpy as np
import serial, time
from termcolor import cprint

def checkCrc(data):
    crc1 = data[-2:]
    crc2 = libscrc.modbus(data[:-2])
    return crc1 == crc2
#################################################################################
# Build motion commands (MODBUS packets) to send to driver.
# These are the default settings in the Leadshine test software.
def motionCommand(revolutions = 1.0, velocity = 120, acceleration = 200, intermission = 1000, repeats=1,\
                  current = 100, reverse = False, bidirectional = False, ESD508_ID = '\x01',\
                  pulses_per_rev = 4000, encoder_resolution = 4000, position_err = 10, **kwargs):
               
    # Commands
    ESD508_WRITE = b'\x06'
    ESD508_READ  = b'\x03'
    
    # Registers
    ESD508_MODE = b'\x09' # RS232 control of motor enabled ??
    ESD508_PREV = b'\x0e' # Motor pulses per revolution [ 0e/0f ? ]
    ESD508_ENCR = b'\x0f' # Encoder resolution per revolution [ 0e/0f ? ]
    ESD508_PERR = b'\x12' # Position error limit
    ESD508_EXEC = b'\x14' # command issued before motor begins to move
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
    
    distance = revolutions * 100 # ?? why is this
    if revolutions < 0:
        reverse = ~reverse
        distance = np.abs(distance)
    
    commands = []
    
    # Set up motor parameters - generally set once
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_PREV, pulses_per_rev))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_PERR, position_err))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_ENCR, encoder_resolution))
    # standard parameter block before each run
    commands.append(struct.pack('>ccxcx?',ESD508_ID, ESD508_WRITE, ESD508_DIRN, ~reverse))
    commands.append(struct.pack('>ccxcx?',ESD508_ID, ESD508_WRITE, ESD508_BIDR, bidirectional))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_ACCL, acceleration))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_DIST, distance))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_INTR, intermission))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_NREP, repeats))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_VELO, velocity))
    commands.append(struct.pack('>ccxcH', ESD508_ID, ESD508_WRITE, ESD508_CURR, current))
    # commands to start the motion
    commands.append(struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, b'\x41', True))     # ?
    commands.append(struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, b'\x42', False))    # ?
    commands.append(struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, ESD508_MODE, True)) # test motion
    commands.append(struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, ESD508_EXEC, True)) # execute
    
    # Now make command set for checking when we expect encoder data to be ready
    enquire_loop  = struct.pack('>ccxcx?',ESD508_ID, ESD508_READ, ESD508_ENQR, True) # ask if ready
    enquire_wait  = struct.pack('>cc3s',ESD508_ID, ESD508_READ, ESD508_WAIT) # not ready
    enquire_ready = struct.pack('>cc3s',ESD508_ID, ESD508_READ, ESD508_DATA) # yes ready
    enquire_send  = struct.pack('>ccxcH', ESD508_ID, ESD508_READ, ESD508_EXEC, 200) # send 200 encoder data points
    cleanup = struct.pack('>ccxcx?', ESD508_ID, ESD508_WRITE, ESD508_MODE, False) # end RS232 control program
    
    # add checksums.
    setup_commands = []
    for c in commands:
        crc = libscrc.modbus(c)
        setup_commands.append(c + struct.pack('H',crc))
        
    loop_commands = []
    for c in [ enquire_loop, enquire_wait, enquire_ready, enquire_send, cleanup ]:
        crc = libscrc.modbus(c)
        loop_commands.append( c + struct.pack('H',crc))
    
    return setup_commands, loop_commands
                  
#################################################################################
# Modbus write and readback to check command was received and acted upon
def writeAndVerify(serialPort, cmd, sleeptime, debugMode=True):
    # Write command
    serialPort.write(cmd)
    # Wait
    time.sleep(sleeptime)
    # Read back same # bytes
    readback = serialPort.read(len(cmd))
    if debugMode: print("\twrote %s / read %s" % (binascii.hexlify(cmd),binascii.hexlify(readback)))
    # Confirm checksum ok
    data = readback[:-2]
    crc1 = readback[-2:]
    crc2 = struct.pack('H',libscrc.modbus(data))
    #if debugMode: print("\t\tCRC = %s / %s" % (binascii.hexlify(crc1),binascii.hexlify(crc2)))
    
    return crc1==crc2


#################################################################################
# ES-D508 control routine.  Move motor and return servo data from driver buffer.
# S is the (already opened) pySerial class instance.
def move_servomotor(S, verbose=True, debugMode=False, sleeptime=0.001, maxlen=65535, **kwargs):

    ENCODER_CAL_DEFAULT = 89211. #42518 #78912

    # Make command set
    setup_commands, loop_commands = motionCommand(**kwargs)
    enquire_loop, enquire_wait, enquire_ready, enquire_send, cleanup = loop_commands
    
              
    # Send setup commands
    for cmd in setup_commands:
        if not writeAndVerify(S,cmd,sleeptime,debugMode): raise IOError("Communication failed")
        time.sleep(sleeptime)
    
    # Motion happens now.
    cprint("\tMoving servomotor...",'green')
    
    # Go into a loop to wait for encoder data to come back.
    enc_data = []
    try:
        while True:
        
            # Loop until ready to receive data
            in_loop = True
            t0 = time.time()
            while in_loop:
                # ask if ready
                S.write(enquire_loop)
                if debugMode: print("\twrote %s ENQUIRE" % binascii.hexlify(enquire_loop))
                time.sleep(sleeptime)
                # Check response
                readback = S.read(len(enquire_wait))
                if readback == enquire_ready:
                    in_loop = False
                    if debugMode: print("\tread %s READY\n" % binascii.hexlify(readback))
                elif readback == enquire_wait:
                    if debugMode: print("\tread %s WAIT" % binascii.hexlify(readback))
                else:
                    if debugMode: print("\t%s ???? (%s or %s)" % (binascii.hexlify(readback),binascii.hexlify(enquire_ready),binascii.hexlify(enquire_wait)))
                # Check timeout of loop
                if time.time() - t0 > 5.:
                    if debugMode or verbose: cprint("\tStatus timeout in inner loop!",'red')
                    break
                
            # Read data
            if not in_loop:
                time.sleep(sleeptime)
                S.write(enquire_send)
                if debugMode: print("\t%s RTS" % binascii.hexlify(enquire_send))
                data = ''
                time.sleep(sleeptime)
                data = ''
                crc_ok = False
                # Keep reading until crc is satisfied and length is within bounds
                while (not crc_ok) and (len(data)<maxlen):
                    data += S.read(1)
                    if len(data)>=4:
                        crc1 = data[-2:]
                        crc2 = struct.pack('H',libscrc.modbus(data[:-2]))
                        if crc1 == crc2: crc_ok = True
                    
                
                if debugMode: print("\tread %i bytes" % (len(data)))
                #if debugMode: print(binascii.hexlify(data[3:-2]), len(data[3:-2]))
                n = len(data[3:-2])/2
                shorts = struct.unpack('%ih' % n,data[3:3+2*n])
                enc_data.extend(list(shorts))
                
                # If the last 20 encoder values are the same, we are done sampling.
                if len(np.unique(shorts[-20:]))==1:
                    break
                else:
                    time.sleep(.05)
                
            else:
                if debugMode or verbose: cprint("\tAborting outer loop",'red')
                break
        
            # Loop back to read more data if we reach this point.
        
    except KeyboardInterrupt: # manual aborting data read loop
        time.sleep(0.1)
    
    writeAndVerify(S,cleanup,sleeptime,debugMode)
    if debugMode: print("\n\t%s CLEANUP" % binascii.hexlify(cleanup))

    cprint("\tServomotor stopped.",'green')

    # Process encoder data
    enc_data = np.array(enc_data)
    enc_data -= enc_data[-1]
    
    if not 'encoder_calibration' in kwargs:
        encoder_calibration = ENCODER_CAL_DEFAULT
        cprint("\tEncoder calibration set to default value of %f" % encoder_calibration,'yellow')
    elif kwargs['encoder_calibration'] is None:
        encoder_calibration = ENCODER_CAL_DEFAULT
        cprint("\tEncoder calibration set to default value of %f" % encoder_calibration,'yellow')
    else:
        encoder_calibration = kwargs['encoder_calibration']
    
    enc_pos = np.cumsum(enc_data)/float(encoder_calibration) # convert to revolutions
    
    return enc_pos
    
    
#################################################################################
# This is just for testing.
if __name__ == '__main__':

    # Open serial port
    if debugMode: print("Opening %s" % serialPort)
    S = serial.Serial('/dev/cu.usbserial-AC00I4ZZ',\
                      38400, serial.EIGHTBITS, serial.PARITY_NONE,\
                      serial.STOPBITS_ONE, xonxoff=False, rtscts=False, timeout=1.)
                      
    enc_pos = move_servomotor(S, verbose=True, debugMode=True, revolutions = 1)

    import matplotlib.pyplot as plt
    fig=plt.figure()
    plt.plot(enc_pos)
    plt.show()
    exit()

