import usb.core
for dev in usb.core.find(find_all=True): 
	serial_number=None;manufacturer=None
	try: serial_number=dev.serial_number
	except: pass
	try: manufacturer=dev.manufacturer
	except: pass
	print 'bus=%03i address=%03i : vid=0x%04x pid=0x%04x : class=0x%02x device=0x%04x serial=%s manuf=%s' % (dev.bus, dev.address, dev.idVendor, dev.idProduct,dev.bDeviceClass,dev.bcdDevice,serial_number,manufacturer)
