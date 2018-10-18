#!/usr/bin/env python
import sys, struct
out=sys.stdout

with open('ttyUSB0.log','rb') as f:
    i=0
    while True:
        b=f.read(1)
        if not b: break
        if b=='(': 
            mode=f.read(3).strip()
            data=''

            if mode[0]=='P':

                f.read(2) # dump bytes from interceptty
                b=f.read(1)

                while b!='(':
                    data+=b
                    b=f.read(1)
                    if b=='>' or b=='\t' or b=='\n': b='' # interceptty formatting stripped out
                    if b=='<': break # computer sent command, data stream stopped.

                data=data.strip()
                decoded=bytearray.fromhex(data.replace('0x',''))
                
                print "MODE=",mode,"DATA=",data
                print "\t\t", struct.unpack('f', decoded[:5])

print "\nDone."
