#!/usr/bin/env python3


'''
import cp2110

usb_info = cp2110.enumerate()

# Initialize device
try:
    d = cp2110.CP2110Device(path=b'/dev/hidraw4')
    
    # Configure UART
    d.set_uart_config(cp2110.UARTConfig(
        baud=19200,
        parity=cp2110.PARITY.ODD,
        flow_control=cp2110.FLOW_CONTROL.DISABLED,
        data_bits=cp2110.DATA_BITS.SEVEN,
        stop_bits=cp2110.STOP_BITS.SHORT))
    
    #print(d.is_uart_enabled())
    d.enable_uart()
    
    # Write data
    #d.write(b'\x00')
    # Read data
    data = d.read(14)
    print(repr(data))
except Exception as e:
    raise
    print(f"Error: {e}")


'''
import serial, hid

hid_devs=hid.enumerate()
for hd in hid_devs:
    if 'CP2110' in hd['product_string'].upper():
        hid_path=hd['path']
        for key in hd.keys(): print('\t%s: %s' % (key,hd[key]))
        break
    
port="cp2110://"+hid_path.decode('ascii')


with serial.serial_for_url(port,baudrate=19200,bytesize=serial.SEVENBITS,parity=serial.PARITY_ODD,\
                           stopbits=serial.STOPBITS_ONE,timeout=2,rtscts=False,dsrdtr=False,xonxoff=False) as s:
    for n in range(4):
        s._dtr_state=bool(n%2)
        s._rts_state=bool(n/2)
        s.write(b'\x00')
        print(s._dtr_state, s._rts_state)
        data=s.read(14)
        print(len(data),repr(data))
