#!/usr/bin/env python
import numpy as np

# String name, int hashSize, long poly, long init, boolean refIn, boolean refOut, long xorOut, long check)
# AlgoParams("CRC-16/MODBUS", 16, 0x8005, 0xFFFF, true, true, 0x0, 0x4B37);

import binascii


def crc16(data):
    '''
    CRC-16-ModBus Algorithm
    '''
    
    
    #for index in xrange(len(data)):
    #    data[index] = (data[index] * 0x0202020202 & 0x010884422010) % 1023;
    #    data[index] ^= 0xFF
        
    
    
    '''
    for (int i = valueLength - 1; i >= 0; i--)
    {
        newValue |= (ul & 1) << i;
        ul >>= 1;
    }
    '''
    
    poly = 0x8005 #0x8404
    crc = 0xFFFF #0x0000
    for b in data:
        crc ^= (0xFF & b)
        for _ in range(0, 8):
            if (crc & 0x0001):
                crc = ((crc >> 1) & 0xFFFF) ^ poly
            else:
                crc = ((crc >> 1) & 0xFFFF)
    
    # reverse byte order if you need to
    #crc = (crc << 8) | ((crc >> 8) & 0xFF)

    #bin_number = bin(np.uint16(crc))
    #reverse_number = bin_number[-1:1:-1]
    #reverse_number = reverse_number + (16 - len(reverse_number))*'0'

    return np.uint16(crc)
    
input = '0106001c0000'
output = bytearray.fromhex(input)

# do it for me
print("                 480c")
print("{} --> {} - {}".format(input, binascii.hexlify(crc16(output)), crc16(output)))
