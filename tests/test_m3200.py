#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test MEAS M32JM Pressure sensor i2c communications via i2c FTDI bridge.
   
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 13/06/25

    Multiphase Flow Laboratory
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
"""

import i2cdriver
import time, struct

# Initialize I2C bus over USB bridge
i2c = i2cdriver.I2CDriver("/dev/ttyUSB0")


# M32JM sensor address (check datasheet, often 0x28 for TE pressure sensors)
sensor_address = 0x28

try:
    while True:
        
        status=2
        
        while status != 0:
            i2c.start(sensor_address,1)
            time.sleep(0.3)
            data=i2c.read(4)
            #time.sleep(0.1)
            i2c.stop()

            #print(f"Raw Data: {data}") 

            rawP,rawT=struct.unpack('>HH',data)

            #print(f"Raw Data: {rawP}   {rawT}") 

            status=rawP >> 14
        rawP = rawP & 0x3FFF
        rawT = rawT >> 5

        maxPressure=100
        pressure = ((rawP - 1000.0) / (15000.0 - 1000.0)) * maxPressure;
        temperature = ((rawT - 512.0) / (1075.0 - 512.0)) * 55.0;
        print("Status=%i,\tPressure=%+f\tTemperature=%+f\t%s" % (status,pressure,temperature,data))
        
        time.sleep(0.1)
        
except KeyboardInterrupt:
    exit()
    
