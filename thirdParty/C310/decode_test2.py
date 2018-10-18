#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, struct
import numpy as np

out=sys.stdout

with open('ttyUSB0.log','rb') as f:
    i=0
    while True:
        b=f.read(1)
        if not b: break
        if b=='(': 
            mode=f.read(5).strip()
            data=''
            
            '''
            Software transmits 0x41 (A)\n to request a normal report. or 0x4b (K)\n for the model number.
            The meter responds with 0x02 0x50 (ModeChar) and then a sequence of strings containing
            hex data in ASCII format seperated by \n each. There are 4 to 9 bytes returned depending on the meter's operating mode.
            
            ModeChar represents the mode of the meter, as follows:
            Mode 'P' is a normal report of humidity, temperature in C, and time in free run mode.
            Mode 'H' is normal free run in Farenheit.
            Mode 'Q' is MAX
            Mode 'R' is MIN
            Mode 'S' is MAX MIN
            Mode 'T' is HOLD
            '''
            
            if mode[0]=='K':
                # ID report
                print mode[:2], f.read(43).replace('>','').replace('\t','').replace('\n','').replace('<','').strip()
            
            elif mode[0]!='A':
                sys.stdout.write(' ')
                b=f.read(1)
                while b!='(':
                    data+=b
                    b=f.read(1)
                    if b=='>' or b=='\t' or b=='\n': b='' # interceptty formatting stripped out
                    if b=='<': break # computer sent command, data stream stopped.

                data=data.strip()
                try:
                    decoded=bytearray.fromhex(data.replace('0x',''))
                except ValueError as e:
                    print 'MODE=',mode, 'DATA=',data
                    raise
                
                # Now decode the byte string.
                humidity = -1
                temperature = -1
                time_min = 0
                time_sec = 0
                flags = None
                if len(decoded)>=4:
                    humidity, temperature = np.array(struct.unpack('>2H', decoded[1:5]))/10.
                if len(decoded)>=7:
                    time_min, time_sec = np.array(struct.unpack('>bb', decoded[5:7]))
                if len(decoded)>=8:
                    flags = decoded[7:]
                
                
                if len(decoded)>=6:
                    print "MODE=",mode[0],"DATA=",data,"\t %02.1f%% %02.1fºC %02i:%02i" % (humidity,temperature,time_min,time_sec), flags

            else:
                sys.stdout.write(mode[:2])


print "\nDone."
