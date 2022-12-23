#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test Center 310 PTH meter experimental driver.

   
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2023 LTRAC
    @license GPL-3.0+
    @version 1.3.0
    @date 23/12/2022
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
"""


import numpy as np
import struct

class mytest:
  def __init__(self):
    self.params={}; self.config={}
    self.name = "Center 310 Humidity/Temperature meter"
    self.config['channel_names']=['humidity','temperature','timer','hold','min_max']
    self.params['raw_units']=['%','','s','',''] # temp units will be determined when query runs
    self.config['eng_units']=['%','','s','','']
    self.config['scale']=[1.,1.,1.,1.,1.]
    self.config['offset']=[0.,0.,0.,0.,0.]
    self.params['n_channels']=5
    self.serialQuery=['A'] # This will return everything except the model number
    self.queryTerminator='\r\n'
    self.responseTerminator='\x03' # The "K" query terminates in \r\n but the "A" terminates in 0x03
    self.params['min_response_length']=4 # bytes
  def decode(self,rawData):

    print '\t0x'+rawData[0].encode('hex') # Debugging
    hold=0; minmax=0; prefix_data=''
    while (rawData[0][0] != '\x02') and (rawData[0][1] < '\x41'):
        # Advance forwards in the string until we find 0x02 followed by an ASCII capital letter.
        # Put everything before this into 'prefix_data' for later processing.
        prefix_data += rawData[0][0]
        rawData[0] = rawData[0][1:]
    # Get the mode string
    mode = rawData[0][1].strip()
    # Determine the units, hold and minmax values from the mode string
    if 'P' in mode: self.params['raw_units'][1]='C'
    elif 'T' in mode: hold=1
    elif 'R' in mode: minmax=1
    elif 'Q' in mode: minmax=2
    elif 'S' in mode: minmax=3
    elif 'H' in mode: self.params['raw_units'][1]='F'
    elif '\x10' in mode: pass
    else:
        print "\t!! Unknown device mode string in serial response"
        raise ValueError
    if len(rawData[0])<6: raise ValueError # Short/corrupted responses.
    decoded=rawData[0][2:] # Everything after the mode string is T&H data
    humidity = np.nan; temperature = np.nan # Default to NaN
    time_min = np.nan; time_sec = np.nan
    flags = None

    if mode is 'H': # Farenheit mode puts the timer data before the mode string
        humidity = np.array(struct.unpack('>H', decoded[1:3]))[0]/10.
        temperature = np.array(struct.unpack('>H', decoded[3:]+'\x00'))[0]/10.
        if len(prefix_data) > 2:
            time_min, time_sec = np.array(struct.unpack('>bb', prefix_data[-3:-1]))
    else: # Celsius mode
        if len(decoded)>4:
            humidity, temperature = np.array(struct.unpack('>2H', decoded[1:5]))/10.
        if len(decoded)>=7:
            time_min, time_sec = np.array(struct.unpack('>bb', decoded[5:7]))
        if len(decoded)>=8:
            flags = decoded[7:] # Flag tells us if a mode change is going to happen
    self.params['mode']=mode.strip()
    if flags is None: self.params['flags']=''
    else: self.params['flags']=flags.strip()
    return [humidity, temperature, time_min*60 + time_sec, hold, minmax]


try:
    obj = mytest()
    obj.lastValue = obj.decode(['\x02\x10\x00\x01\xc8\x01\x0e\x00\x00\x03'])
    for i in range(obj.params['n_channels']):
        print obj.config['channel_names'][i], obj.lastValue[i], obj.params['raw_units'][i]
except:
    raise
