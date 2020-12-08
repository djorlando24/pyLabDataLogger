#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test Status SEM1600B experimental driver.

   
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @version 1.0.3
    @date 07/12/2020
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
print dev
if dev is None: raise ValueError("Device not found.")

dev.reset()

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

# Set the active configuration (default)
#dev.set_configuration()


print ''
print '=+'*40
print ''



# Loop to read streaming data back
meas_prev=0; meas_num=0
while True:

    # Send control bytes
    #request = '\x01\x04\x28\x00\x00\x98\xf8\x00' 
   
    #help(dev.ctrl_transfer)
    #exit()

    #ctrl_transfer(self, bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength=None, timeout=None)
    #print dev.ctrl_transfer(0xc0,144,0x0000,0x003f,2)
    #print repr(dev.read(0x81, 2, timeout=1000))
    
    #print dev.ctrl_transfer(0x40,0x0,0x0,0x0,0x0)
    #print "%i bytes sent: %s" % (len(request),repr(request))
    #print repr(dev.read(0x81, 2, timeout=1000))

    # Sent URB_BULK out
    #write(self, endpoint, data, timeout=None)
    for n in range(1):
        dev.write(0x02, '\x01\x04\x28\x00\x00\x98\xf8\x00',100)
        time.sleep(.1)

    # Read data back
    s=''
    while len(s)<128:
        try:
            buf = array.array('B','')
            buf = dev.read(0x81, 2, timeout=100)
            s+=''.join(struct.unpack('%ic' % len(buf),buf)) #buf.tostring()
            sys.stdout.write(str(struct.unpack('<h',buf)))
            sys.stdout.flush()
        except usb.core.USBError as e:
            print e
            break
    print ""
    print repr(s).replace('\\x','')

    exit()

    '''
    if len(s)>=64:
        # Extraction of values. Little endian floats are buried inside the byte string. We'll ignore the checksum for now.
        dvid = repr(s[:3]).replace('\\x','')
        emis = struct.unpack('<f',s[25:25+4])[0]
        tmin = struct.unpack('<f',s[36:36+4])[0]
        tcur = struct.unpack('<f',s[48:48+4])[0]
        tmax = struct.unpack('<f',s[42:42+4])[0]
        delt = struct.unpack('<f',s[54:54+4])[0]
        meas_id = struct.unpack('<L',s[6:6+4])[0]
        if s[29]==' ': ttrm = struct.unpack('<f',s[31:31+4])[0]
        else: ttrm=np.nan
        flags = struct.unpack('8B',s[56:64])
        if flags[4] == 1: units = 'degC'
        elif flags[4] == 2: units = 'degF'
        else: units = '?'
        if (emis<0.) | (emis>1.): emis=np.nan
        if (tmin<-999) | (tmin>999): tmin=np.nan
        if (tmax<-999) | (tmax>999): tmin=np.nan
        if (tcur<-999) | (tcur>999): tmin=np.nan
        print "%i) Dev=%s Tmin = %f, Tcur = %f, Tmax = %f, e = %f, DeltaT = %f, thermocouple = %f, units = %s" % (meas_id,dvid,tmin,tcur,tmax,emis,delt,ttrm,units)
        
        
        # Debugging
        for n in range(len(s)-3):     # Find floats
            v=struct.unpack('<f',s[n:n+4])[0]
            if (v>0.01) & (v<500):
                print n,'\t',v 
        exit()
    '''
        
    
    print 
    
    #time.sleep(.1)
