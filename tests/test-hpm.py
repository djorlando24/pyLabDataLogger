#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test program to read HPMA particle sensor via Raspi UART
# D Duke

import serial
import binascii
import time
import sys
import struct

# serial0 is for the raspberry pi's UART pins 4-5.
# Timeout is very important for this to work.
s=serial.Serial('/dev/serial0',9600,8,'N',1,timeout=0.1)

# Stop Auto Send
print("Stop Auto Send")
print(s.write([0x68,0x01,0x20,0x77]))
print(binascii.hexlify(s.read(5)))  # 0xA5A5 = success

try:
	while (True):
		print("Write %i bytes" % s.write([0x68,0x01,0x04,0x93]))

		print("Read:")
		header=bytes(s.read(2))

		if header==b'\x96\x96':
			print("Negative ACK")
		elif header==b'\x40\x05':
			print("Positive ACK")
			data=bytes(s.read(36))
			print("\tData: (received %i bytes)" % len(data))
			#pm25d = data[1]*256 + data[2]
			#pm10d = data[3]*256 + data[4]
			pm25 = str(struct.unpack('>h',data[1:3])[0])+' ug/m3'
			pm10 = str(struct.unpack('>h',data[3:5])[0])+' ug/m3'
			cs1 = data[5]
			cs2 = (65536-(int(header[0])+int(header[1])+int(data[0])+sum([int(v) for v in data[1:5]])))%256
			print("\tPM2.5 = %s\n\tPM10 = %s\n\tChecksum match=%s\n" % (pm25,pm10,cs1==cs2))
		else:
			print(binascii.hexlify(header))
			print("? cannot decode")

		'''
		b=' '
		while len(b)>0:
			b=s.read(1)
			sys.stdout.write(str(binascii.hexlify(b))[2:4])
			sys.stdout.flush()
			#d+=str(binascii.hexlify(b))
		'''
		print("---")
		time.sleep(1.0)

except KeyboardInterrupt:
	pass

s.close()
