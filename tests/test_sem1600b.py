#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test Status SEM1600B experimental driver.

   
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.0
    @date 20/12/2020
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

'''
Bus 001 Device 006: ID 0403:bab1 Future Technology Devices International, Ltd 
Device Descriptor:
  bLength                18
  bDescriptorType         1
  bcdUSB               2.00
  bDeviceClass            0 
  bDeviceSubClass         0 
  bDeviceProtocol         0 
  bMaxPacketSize0         8
  idVendor           0x0403 Future Technology Devices International, Ltd
  idProduct          0xbab1 
  bcdDevice            6.00
  iManufacturer           1 Process Device
  iProduct                2 BRIDGE AMP
  iSerial                 3 DIN_BRG
  bNumConfigurations      1
  Configuration Descriptor:
    bLength                 9
    bDescriptorType         2
    wTotalLength       0x0020
    bNumInterfaces          1
    bConfigurationValue     1
    iConfiguration          0 
    bmAttributes         0x80
      (Bus Powered)
    MaxPower               20mA
    Interface Descriptor:
      bLength                 9
      bDescriptorType         4
      bInterfaceNumber        0
      bAlternateSetting       0
      bNumEndpoints           2
      bInterfaceClass       255 Vendor Specific Class
      bInterfaceSubClass    255 Vendor Specific Subclass
      bInterfaceProtocol    255 Vendor Specific Protocol
      iInterface              2 BRIDGE AMP
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x81  EP 1 IN
        bmAttributes            2
          Transfer Type            Bulk
          Synch Type               None
          Usage Type               Data
        wMaxPacketSize     0x0040  1x 64 bytes
        bInterval               0
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x02  EP 2 OUT
        bmAttributes            2
          Transfer Type            Bulk
          Synch Type               None
          Usage Type               Data
        wMaxPacketSize     0x0040  1x 64 bytes
        bInterval               0
can't get device qualifier: Resource temporarily unavailable
can't get debug descriptor: Resource temporarily unavailable
Device Status:     0x0000
  (Bus Powered)

'''

import usb.core
import usb.util
import sys, time, binascii, array, struct
import numpy as np

# find device
dev = usb.core.find(idVendor=0x0403, idProduct=0xbab1)

# was it found?
print(dev)
if dev is None: raise ValueError("Device not found.")


# Make sure OS kernel isn't hogging the device
for cfg in dev: 
  for intf in cfg: 
    if dev.is_kernel_driver_active(intf.bInterfaceNumber):
        try:
            dev.detach_kernel_driver(intf.bInterfaceNumber)
        except usb.core.USBError as e:
            sys.exit("Could not detatch kernel driver from interface({0}):{1}".format(intf.bInterfaceNumber, str(e)))

# Claim the interface 0 of the device
usb.util.claim_interface(dev, 0)
dev.reset()

# Set the active configuration (default)
#dev.set_configuration()


print('')
print('=+'*40)
print('')



# Loop to read streaming data back
meas_prev=0; meas_num=0
while True:

    
    # Send control bytes
    if meas_num==0:
        #         ctrl_transfer(self, bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength=None, timeout=None)
        assert dev.ctrl_transfer(      0x40,          0,        0x0001,   0x0000, 8,timeout=100) == 8
        time.sleep(.05)
        assert dev.ctrl_transfer(      0x40,          3,        0x809c,   0x0000, 8,timeout=100) == 8
        time.sleep(.05)
        assert dev.ctrl_transfer(      0x40,          4,        0x0008,   0x0000, 8,timeout=100) == 8
        time.sleep(.05)
        assert dev.ctrl_transfer(      0x40,          2,        0x0000,   0x0000, 8,timeout=100) == 8
        time.sleep(.05)
        assert dev.ctrl_transfer(      0x40,          9,        0x0003,   0x0000, 8,timeout=100) == 8
        time.sleep(.05)

    #data=[]

    #for nn in range(2):
    
    # Sent URB_BULK out
    #   write(self, endpoint, data, timeout=None)
    #dev.write(0x02, "\x01\x04\x28\x00\x00\x98\xf8\x00", 100)
    dev.write(0x02, b'\x01\x04\x28\x00\x00\x98\xf8\x00', 100)
    time.sleep(.01)
    
    # Read data back
    s=b''; empties=0
    while len(s)<14:
        try:
            buf = b'' #array.array('B','')
            buf = dev.read(0x81, 128, timeout=100)
            #time.sleep(.01)
            s+=buf #struct.unpack('%ic' % len(buf),buf)) #buf.tostring()
            #data.append(buf)
            #sys.stdout.write(repr(buf))
            #sys.stdout.write('\n')
            #sys.stdout.flush()
            if buf == b'': #array.array('B',[1,96]): 
                empties+=1 # This is an empty return string
            else: 
                empties=0
            if empties>1000: break
        except usb.core.USBError as e:
            print(e)
            break
    
    print("")
    time.sleep(.1)

    print(len(s),'bytes received:', repr(s))
    #s=s[2:] # discard \x01 \x60 header
  
    ''' 
    for offset_byte in range(8): 
       for endianness in ('<','>'):
         for typ,so in (('h',2),('H',2),('i',4),('I',4),('l',4),('L',4),('q',8),('Q',8),('f',4),('d',8)):
            n=int(len(s)/so)
            print(offset_byte,endianness,typ,':',struct.unpack('%s%i%s' % (endianness, n,typ),s[:so*n]))
       s=s[1:]
    '''

    #if len(s)>=14:
    #    print(struct.unpack('<HHff',s[1:1+12]))

    if len(s)>=26:
        # Extraction of values. Little endian floats are buried inside the byte string. We'll ignore the checksum for now.
        '''
        raw = struct.unpack('<f',s[ 5: 5+4])[0]
        inp = struct.unpack('<f',s[ 9: 9+4])[0]
        pro = struct.unpack('<f',s[13:13+4])[0]
        per = struct.unpack('<f',s[17:17+4])[0]
        out = struct.unpack('<f',s[21:21+4])[0]
        flt = struct.unpack('<f',s[25:25+4])[0]
       
        print("Raw=%f, Input=%f, Filtered Input=%f, Process=%f, PercentOutput=%f, OutputSignal=%f" % (raw,inp,flt,pro,per,out))
        '''
        o=2
        n=int((len(s)-o)/4)
        data=struct.unpack('<%if' % n,s[o:o+4*n])
        
        #data=struct.unpack('<8f',s[2:2+4*8])
        #print(data[:8],b''.join(data[8:]))
        print(data)
    
    print() 

    meas_num+=1
    #break 
    time.sleep(.25)
