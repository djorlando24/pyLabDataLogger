#!/usr/bin/env python3
'''
This script was modified to run on python3.
The original code is reused from ControlEverything under these terms:

    # Distributed with a free-will license.
    # Use it any way you want, profit or free, provided it fits in the licenses of its associated works.

    # H3LIS331DL
    # This code is designed to work with the H3LIS331DL_I2CS I2C Mini Module available from ControlEverything.com.
    # https://www.controleverything.com/content/Accelorometer?sku=H3LIS331DL_I2CS#tabs-0-product_tabset-2

It's found at https://github.com/ControlEverythingCommunity/H3LIS331DL
'''

import smbus
import time

# Get I2C bus
bus = smbus.SMBus(1)
adds = 0x19

# H3LIS331DL address, 0x18(24)
# Select control register 1, 0x20(32)
#		0x27(39)	Power ON mode, Data output rate = 50 Hz
#					X, Y, Z-Axis enabled
bus.write_byte_data(adds, 0x20, 0x27)
# H3LIS331DL address, 0x18(24)
# Select control register 4, 0x23(35)
#		0x00(00)	Continuous update, Full scale selection = +/-100g
bus.write_byte_data(adds, 0x23, 0x00)

time.sleep(0.5)

while True:
    
    # H3LIS331DL address, 0x18(24)
    # Read data back from 0x28(40), 2 bytes
    # X-Axis LSB, X-Axis MSB
    data0 = bus.read_byte_data(adds, 0x28)
    data1 = bus.read_byte_data(adds, 0x29)
    
    # Convert the data
    xAccl = data1 * 256 + data0
    if xAccl > 32767 :
    	xAccl -= 65536

    # H3LIS331DL address, 0x18(24)
    # Read data back from 0x2A(42), 2 bytes
    # Y-Axis LSB, Y-Axis MSB
    data0 = bus.read_byte_data(adds, 0x2A)
    data1 = bus.read_byte_data(adds, 0x2B)
    
    # Convert the data
    yAccl = data1 * 256 + data0
    if yAccl > 32767 :
	    yAccl -= 65536
    
    # H3LIS331DL address, 0x18(24)
    # Read data back from 0x2C(44), 2 bytes
    # Z-Axis LSB, Z-Axis MSB
    data0 = bus.read_byte_data(adds, 0x2C)
    data1 = bus.read_byte_data(adds, 0x2D)
    
    # Convert the data
    zAccl = data1 * 256 + data0
    if zAccl > 32767 :
	    zAccl -= 65536

    # Output data to screen
    print( "Acceleration X, Y, Z : %d, %d, %d" % (xAccl,yAccl,zAccl) )

    time.sleep(.1)

