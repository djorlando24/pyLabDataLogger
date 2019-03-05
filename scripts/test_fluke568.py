#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test FLUKE 568 experimental driver.

   
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 01/03/2019
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""


"""
Bus 003 Device 015: ID 0f7e:9002 Fluke Corp. 
Couldn't open device, some information will be missing
Device Descriptor:
  bLength                18
  bDescriptorType         1
  bcdUSB               2.00
  bDeviceClass            0 (Defined at Interface level)
  bDeviceSubClass         0 
  bDeviceProtocol         0 
  bMaxPacketSize0         8
  idVendor           0x0f7e Fluke Corp.
  idProduct          0x9002 
  bcdDevice            0.00
  iManufacturer           1 
  iProduct                2 
  iSerial                 0 
  bNumConfigurations      1
  Configuration Descriptor:
    bLength                 9
    bDescriptorType         2
    wTotalLength           34
    bNumInterfaces          1
    bConfigurationValue     1
    iConfiguration          0 
    bmAttributes         0x80
      (Bus Powered)
    MaxPower              100mA
    Interface Descriptor:
      bLength                 9
      bDescriptorType         4
      bInterfaceNumber        0
      bAlternateSetting       0
      bNumEndpoints           1
      bInterfaceClass         3 Human Interface Device
      bInterfaceSubClass      0 No Subclass
      bInterfaceProtocol      0 None
      iInterface              0 
        HID Device Descriptor:
          bLength                 9
          bDescriptorType        33
          bcdHID               1.11
          bCountryCode           33 US
          bNumDescriptors         1
          bDescriptorType        34 Report
          wDescriptorLength      32
         Report Descriptors: 
           ** UNAVAILABLE **
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x81  EP 1 IN
        bmAttributes            3
          Transfer Type            Interrupt
          Synch Type               None
          Usage Type               Data
        wMaxPacketSize     0x0008  1x 8 bytes
        bInterval              10
"""

import usb.core
import usb.util
import sys, time, binascii, array

# find device
# Bus 003 Device 014: ID 0f7e:9002 Fluke Corp. 
dev = usb.core.find(idVendor=0x0f7e, idProduct=0x9002)

# was it found?
print dev
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

# Set the active configuration (default)
#dev.set_configuration()


print ''
print '=+'*40
print ''



# Loop to read streaming data back
while True:

    # Send control bytes
    request = '\x81\x02\x05\x00\x00\x00\x00\x00'
    assert dev.ctrl_transfer(0x21,0x09,0x0200,0x0000,request)==len(request)
    #print "%i bytes sent: %s" % (len(request),repr(request))

    s=''
    while True:
        try:
            buf = array.array('B','')
            buf = dev.read(0x81, 64, timeout=100)
            s+=buf.tostring()
        except usb.core.USBError as e:
            break    

    # Convert to byte string


    # Show the contents
    #print binascii.hexlify(s)
    print repr(s)#.replace('\\x',' 0x')
    
    time.sleep(.1)

"""
# get an endpoint instance
cfg = dev.get_active_configuration()
intf = cfg[(0,0)]

ep = usb.util.find_descriptor(
        intf,
        # match the first OUT endpoint
        custom_match = \
        lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_OUT)

assert ep is not None
"""
