#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test Cozir CO2 sensor on Raspberry pi UART
# D Duke

import serial
import time
s=serial.Serial('/dev/ttyUSB0',9600,8,'N',1,timeout=0.1)

# Set polling mode
s.write('K 2\r\n'.encode())
print(s.read(64))

# Get device info
s.write('Y\r\n'.encode())
print(s.read(64))

# Set calibration to known value
#if input("Set calibration?").upper().strip() == 'Y':
#	s.write('X 409\r\n'.encode())
#	print (s.read(64))
#	exit()

# Get scaling constant
s.write('.\r\n'.encode())
ret = s.read(16)
zconst = float(ret[3:8])

try:
	while (True):
		# Query values
		s.write('Q\r\n'.encode())
		data=str(s.read(64))
		print(data)
		l=data.strip().replace("\\r\\n","").strip('\'').split(' ')
		#print(l)
		h=float(l[2]) * 0.1
		t=float(l[4][2:]) * 0.1
		z1=float(l[6][2:])  * zconst
		z2=float(l[8][2:])  * zconst
		print("\tHumidity = %i %%\n\tTemperature = %f degC\n\tCO2 = %i / %i ppm\n" % (h,t,z1,z2)) 
		time.sleep(1.0)
except KeyboardInterrupt:
	pass

s.close()
