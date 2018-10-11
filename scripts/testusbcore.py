import usb.core
for dev in usb.core.find(find_all=True): print 'bus=%03i address=%03i : vid=0x%04x pid=0x%04x : class=0x%02x device=0x%04x serial=%s' % (dev.bus, dev.address, dev.idVendor, dev.idProduct,dev.bDeviceClass,dev.bcdDevice,dev.serial_number)
