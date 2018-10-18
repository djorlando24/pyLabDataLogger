#!/usr/bin/env python
import sys, struct
out=sys.stdout

with open('ttyUSB0.log','rb') as f:
    i=0
    while True:
        b=f.read(1)
        if not b: break
        if b=='(': 
            mode=f.read(6).strip()
            data=''

            if mode[0]=='P':
                b=f.read(1)
                while b!='(':
                    data+=b
                    b=f.read(1)
                    if b=='>' or b=='\t' or b=='\n': b='' # interceptty formatting stripped out
                    if b=='<': break # computer sent command, data stream stopped.

                data=data.strip()
                decoded=bytearray.fromhex(data.replace('0x',''))
                
                
                if len(decoded)>=6:
                    print "MODE=",mode[0],"DATA=",data,"\t", struct.unpack('>2H', decoded[1:5]),\
                                                         struct.unpack('>H', decoded[5:7])


print "\nDone."
