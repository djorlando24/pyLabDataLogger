#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Test Tenma 72-7712 direct USB HID driver.

   
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.0
    @date 27/04/2021
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
Bus 003 Device 005: ID 1a86:e008 QinHeng Electronics HID-based serial adapater
Device Descriptor:
  bLength                18
  bDescriptorType         1
  bcdUSB               1.00
  bDeviceClass            0 
  bDeviceSubClass         0 
  bDeviceProtocol         0 
  bMaxPacketSize0         8
  idVendor           0x1a86 QinHeng Electronics
  idProduct          0xe008 HID-based serial adapater
  bcdDevice           13.00
  iManufacturer           1 (error)
  iProduct                2 (error)
  iSerial                 0 
  bNumConfigurations      1
  Configuration Descriptor:
    bLength                 9
    bDescriptorType         2
    wTotalLength       0x0029
    bNumInterfaces          1
    bConfigurationValue     1
    iConfiguration          4 (error)
    bmAttributes         0x80
      (Bus Powered)
    MaxPower              100mA
    Interface Descriptor:
      bLength                 9
      bDescriptorType         4
      bInterfaceNumber        0
      bAlternateSetting       0
      bNumEndpoints           2
      bInterfaceClass         3 Human Interface Device
      bInterfaceSubClass      0 
      bInterfaceProtocol      0 
      iInterface              0 
        HID Device Descriptor:
          bLength                 9
          bDescriptorType        33
          bcdHID               1.00
          bCountryCode            0 Not supported
          bNumDescriptors         1
          bDescriptorType        34 Report
          wDescriptorLength      37
         Report Descriptors: 
           ** UNAVAILABLE **
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x82  EP 2 IN
        bmAttributes            3
          Transfer Type            Interrupt
          Synch Type               None
          Usage Type               Data
        wMaxPacketSize     0x0008  1x 8 bytes
        bInterval               5
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x02  EP 2 OUT
        bmAttributes            3
          Transfer Type            Interrupt
          Synch Type               None
          Usage Type               Data
        wMaxPacketSize     0x0008  1x 8 bytes
        bInterval               5
'''	


import usb.core
import usb.util
import sys, time, binascii, array, struct
import numpy as np


if __name__=='__main__':

    # find device
    dev = usb.core.find(idVendor=0x1a86, idProduct=0xe008)

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
    dev.set_configuration()
    
    print('')
    print('=+'*40)
    print('')

    dev.ctrl_transfer(
          0x21,  # REQUEST_TYPE_CLASS | RECIPIENT_INTERFACE | ENDPOINT_OUT
          9,     # SET_REPORT
          0x300, # "Vendor" Descriptor Type + 0 Descriptor Index
          0,     # USB interface № 0
          b'\x60\x09\x00\x00\x03' # the HID payload as a byte array -- e.g. from struct.pack()
      )

    
    # Loop to read streaming data back
    meas_prev=0; meas_num=0; timeout_ms=50
    while True:

        s=b''
        
        if meas_num==0 :
            dev.write(0x02, b"\x02\x5a\x00\x00\x00\x00\x00\x00", timeout_ms)
            s += dev.read(0x82, 8, timeout_ms)
        
            dev.write(0x02, b"\x01\x01\x00\x00\x00\x00\x00\x00", timeout_ms)
        
        s += dev.read(0x82, 2048, timeout_ms)
        
        
        print("")
        time.sleep(.1)

        #print(len(s),'bytes received:', repr(s))
        


        if len(s)>=19:
            i=0
            buf=b''
            while (i<len(s)):
                # packet decoding
                nbyte = s[i] - 0xf0
                buf += s[i+1:i+1+nbyte]
                i+=8
                # escape on CRLF
                if b'\n' in buf:
                    buf = buf.split(b'\n')[0]
                    break
            # decode payload
            print(repr(buf), buf[1:5])

        meas_num+=1
        time.sleep(0.001)
