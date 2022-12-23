#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    CP2110 HID USB UART BRIDGE TEST
    
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

    Version history:
        DD/MM/YYYY - First version.
"""

import numpy as np
import cp2110

if __name__ == '__main__':

    # This will raise an exception if a device is not found.
    try:
        d = cp2110.CP2110Device(vid=0x10c4, pid=0xea80)
    except:
        raise IOError("Device not found")

    # You can also find a device by path.
    #cp2110.CP2110Device(path='/dev/hidraw0')

    #usb_info = cp2110.enumerate(vid=0x10c4, pid=0xea80)
    #if usb_info:
    #    print(usb_info.as_dict())
    
    
    #19200 7O1 expected for UNI-T D02 type cables
    baud=115200 #19200
    parity=cp2110.PARITY.ODD
    data_bits=cp2110.DATA_BITS.SEVEN
    
    for stop_bits in [cp2110.STOP_BITS.SHORT, cp2110.STOP_BITS.LONG ]:
      for flow_control in [cp2110.FLOW_CONTROL.DISABLED,cp2110.FLOW_CONTROL.ENABLED]:
    #    for parity in [cp2110.PARITY.EVEN, cp2110.PARITY.MARK, cp2110.PARITY.ODD, cp2110.PARITY.SPACE ]:
    #      for data_bits in [ cp2110.DATA_BITS.EIGHT, cp2110.DATA_BITS.FIVE,\
    #                         cp2110.DATA_BITS.SEVEN, cp2110.DATA_BITS.SIX]:
    #        for baud in np.arange(1200,256001,1200):

                # The UART settings are dictated by the device that embeds the CP2110.  It
                # may be configured correctly by default, or you may need to set manually.
                d.set_uart_config(cp2110.UARTConfig(
                    baud=int(baud),
                    parity=parity,
                    flow_control=flow_control,
                    data_bits=data_bits,
                    stop_bits=stop_bits))
                    
                # Fetch the current uart configuration.  This is the UART connection from the
                # CP2110 to the microcontroller (or whatever) it's wired up to.
                c = d.get_uart_config()
                
                # And you can clear any pending data in the on-chip I/O buffers.
                d.purge_fifos()  # The default is cp2110.FIFO.BOTH
                d.purge_fifos(cp2110.FIFO.TX)
                d.purge_fifos(cp2110.FIFO.RX)

                # The UART in your device may need to be explicitly enabled, particularly if
                # you've already explicitly disabled it as in this example.
                #if not d.is_uart_enabled(): d.enable_uart()
                d.enable_uart()
                
                # The write method accepts byte strings or arrays of ints.
                d.write(b'\x06\xab\xcd\x03\x5e\x01\xd9')
                #d.write([0x06,0xab,0xcd,0x03,0x5e,0x01,0xd9])

                # The default read size will return 63 bytes (at most), which is the maximum
                # supported by this chip.  Reads do not block.
                rv = d.read()
                print(c.__dict__)
                if len(rv) > 0:
                    print("\t",repr(rv))
                    print("")
                    d.disable_uart()
                    exit(1)
                
                # If you ever need to disable the UART, you can.
                #d.disable_uart()
