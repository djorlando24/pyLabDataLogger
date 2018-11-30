#!/usr/bin/env python
# This script will test communications with the Omega iSeries process controller via serial port.
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
