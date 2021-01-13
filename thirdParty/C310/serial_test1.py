#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial, time

Serial = serial.Serial(port='/dev/ttyUSB0',baudrate=9600)
responseTerminators=['\r','\x03']
queryTerminator='\r\n'

for serialQuery,responseTerminator in zip(['K','A'],responseTerminators):

    print ("<sent",serialQuery)
    Serial.write((serialQuery+queryTerminator).encode('ascii'))
    time.sleep(0.01)
    s=b''; rawData=[]
    while len(s)<1024:
        s+=Serial.read(1)
        print (s[-1:])
        if s[-1:] == responseTerminator.encode('ascii'):
           rawData.append(s.strip())
           break

    print (">recv",rawData)
