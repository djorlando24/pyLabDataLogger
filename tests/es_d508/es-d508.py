#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Easy Servo Drive ES-D508 RS-232 interface
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2020 LTRAC
    @license GPL-3.0+
    @version 1.1.0
    @date 20/12/2020
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
import libscrc
import numpy as np
from termcolor import cprint
import serial, time

def checkCrc(data):
    crc1 = data[-2:]
    crc2 = libscrc.modbus(data[:-2])
    return crc1 == crc2

# These are the default settings in the Leadshine test software. Do not edit.
def motionCommand(revolutions = 1.0, velocity = 120, acceleration = 200, intermission = 1000, repeats=1,\
                  current = 100, reverse = False, bidirectional = False, ESD508_ID = '\x01',\
                  pulses_per_rev = 4000, encoder_resolution = 4000, position_err = 10):
               
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
    if distance<0:
        distance = -distance
        reverse = ~reverse
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
                  
def writeAndVerify(serialPort, cmd, verbose=True):
    # Write command
    serialPort.write(cmd)
    # Wait
    time.sleep(0.010)
    # Read back same # bytes
    readback = serialPort.read(len(cmd))
    if verbose: print("\twrote %s / read %s" % (binascii.hexlify(cmd),binascii.hexlify(readback)))
    # Confirm checksum ok
    data = readback[:-2]
    crc1 = readback[-2:]
    crc2 = struct.pack('H',libscrc.modbus(data))
    #if verbose: print("\t\tCRC = %s / %s" % (binascii.hexlify(crc1),binascii.hexlify(crc2)))
    
    return crc1==crc2


#################################################################################
# ES-D508 control routine.  Move motor and return servo data from driver buffer
def move_servomotor(serialPort, verbose=True, **kwargs):

    # Make command set
    setup_commands, loop_commands = motionCommand(**kwargs)
    enquire_loop, enquire_wait, enquire_ready, enquire_send, cleanup = loop_commands
    
    # Open serial port
    if verbose: print("Opening %s" % serialPort)
    S = serial.Serial(serialPort,\
                      38400, serial.EIGHTBITS, serial.PARITY_NONE,\
                      serial.STOPBITS_ONE, xonxoff=False, rtscts=False, timeout=1.)
              
    # Send setup commands
    for cmd in setup_commands:
        if not writeAndVerify(S,cmd,verbose): raise IOError("Communication failed")
        time.sleep(0.001)
    
    # Motion happens now.
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
                if verbose: print("\twrote %s ENQUIRE" % binascii.hexlify(enquire_loop))
                time.sleep(0.010)
                # Check response
                readback = S.read(len(enquire_wait))
                if readback == enquire_ready:
                    in_loop = False
                    if verbose: print("\tread %s READY\n" % binascii.hexlify(readback))
                elif readback == enquire_wait:
                    if verbose: print("\tread %s WAIT" % binascii.hexlify(readback))
                else:
                    if verbose: print("\t%s ???? (%s or %s)" % (binascii.hexlify(readback),binascii.hexlify(enquire_ready),binascii.hexlify(enquire_wait)))
                # Check timeout of loop
                if time.time() - t0 > 5.:
                    if verbose: print("\tStatus timeout in inner loop!")
                    break
                
            # Read data
            if not in_loop:
                time.sleep(0.001)
                S.write(enquire_send)
                if verbose: print("\t%s RTS" % binascii.hexlify(enquire_send))
                data = ''
                time.sleep(0.001)
                data = ''
                crc_ok = False
                # Keep reading until crc is satisfied and length is within bounds
                while (not crc_ok) and (len(data)<65535):
                    data += S.read(1)
                    if len(data)>=4:
                        crc1 = data[-2:]
                        crc2 = struct.pack('H',libscrc.modbus(data[:-2]))
                        if crc1 == crc2: crc_ok = True
                    
                
                if verbose: print("\tread %i bytes" % (len(data)))
                #if verbose: print(binascii.hexlify(data[3:-2]), len(data[3:-2]))
                if len(data)%2 == 1:
                    shorts = struct.unpack('%ih' % ((len(data[3:-2])-0)/2),data[3:-2])
                else:
                    shorts = struct.unpack('%ih' % ((len(data[3:-2])-1)/2),data[3:-3])
                
                enc_data.extend(list(shorts))
                
                # If the last 20 encoder values are the same, we are done sampling.
                if len(np.unique(shorts[-20:]))==1:
                    break
                else:
                    time.sleep(.05)
                
            else:
                if verbose: print("\tAborting outer loop")
                break
        
            # Loop back to read more data if we reach this point.
    
    #except KeyboardInterrupt: # manual aborting data read loop
    #    time.sleep(0.1)
    except:
        raise
    
    writeAndVerify(S,cleanup,verbose)
    if verbose: print("\n\t%s CLEANUP" % binascii.hexlify(cleanup))

    # Process encoder data
    enc_data = np.array(enc_data)
    #enc_data -= enc_data[-1]
    enc_pos = np.cumsum(enc_data)/89211. # convert to revolutions
    
    return enc_pos
    
    
#################################################################################
if __name__ == '__main__':
    import scipy.optimize as sopt
    import matplotlib.pyplot as plt
    fig=plt.figure()
    ax1=fig.add_subplot(121)
    plt.xlabel("Time"); plt.ylabel("Encoder value")
    
    ax2=fig.add_subplot(122)
    plt.xlabel("Revolutions"); plt.ylabel("Encoder value")
    
    rvals = np.arange(-1.0,1.01,0.01)
    ans = []
    try:
        for r in rvals:
            cprint("Rotating %f rev" % r, color='cyan')
            enc_pos = move_servomotor('/dev/cu.usbserial-AC00I4ZZ', verbose=False, revolutions = r,\
                                        velocity=50, acceleration=50, intermission=100)
            if len(enc_pos)>0:
                ax1.plot(enc_pos,lw=1,label='%f rev' % r)
                ax2.scatter((r,),(enc_pos[-1],),c='k')
                ans.append(enc_pos[-1])
    except KeyboardInterrupt:
        rvals = rvals[:len(ans)]
        pass
    
    ffit = lambda x,a,b,c:  a*x**2 + b*x + c
    popt, pcov = sopt.curve_fit(ffit, rvals, ans, p0=(0,1,0))
    ax2.plot(rvals, ffit(rvals,*popt),lw=1,ls='--',c='k')
    
    #print "enc_pos = %f * rev + %f" % tuple(popt)
    print popt
    plt.show()
    exit()
