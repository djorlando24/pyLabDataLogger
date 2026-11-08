#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Modbus test for CO2 sensor.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 07/11/2026

    Multiphase Flow Laboratory
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

import sys,time

from pymodbus.client import ModbusSerialClient

import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --- Configuration ---
# Update this string to match your operating system's device path
# Linux: "/dev/ttyUSB0" or "/dev/ttyAMA0"
# Windows: "COM3", "COM4", etc.
# macOS: "/dev/cu.usbserial-XXXX"
SERIAL_PORT = "/dev/cu.usbserial-BG041B3L"

BAUD_RATE = 9600
SLAVE_ID = 32          # Address of the Modbus device
START_REGISTER = 0x00 # Starting register to read
REGISTER_COUNT = 2     # Number of sequential registers to read (0x000 and 0x001)

def main():
    # Initialize the Modbus RTU serial client
    client = ModbusSerialClient(
        port=SERIAL_PORT,
        baudrate=BAUD_RATE,
        bytesize=8,
        parity="N",    # Most common default is None
        stopbits=1,
        timeout=2      # Timeout in seconds to wait for a slave response
    )

    print(f"Connecting to device on {SERIAL_PORT}...")
    if not client.connect():
        print(f"Error: Failed to open serial port {SERIAL_PORT}")
        sys.exit(1)

    try:
        print(f"Reading {REGISTER_COUNT} registers starting at address {hex(START_REGISTER)} from Device {SLAVE_ID}...")
        
        # Read Holding Registers (Function Code 0x03)
        # Change to `read_input_registers` if your device maps them to FC 0x04
        #help(client.read_holding_registers)
        response = client.read_holding_registers(
            address=START_REGISTER,
            count=REGISTER_COUNT,
            device_id=SLAVE_ID
        )

        time.sleep(.05)

        # Check for errors in the protocol response
        if response.isError():
            print(f"Modbus Error: {response}")
        else:
            # Successfully read data
            registers = response.registers
            print("\n--- Successful Read ---")
            print(f"Raw Output Array: {registers}")
            print(f"Register 0x000: {registers[0]} (Hex: {hex(registers[0])})")
            print(f"Register 0x001: {registers[1]} (Hex: {hex(registers[1])})")

    except Exception as e:
        print(f"An error occurred during execution: {e}")
        
    finally:
        # Always close the serial connection safely
        client.close()
        print("\nConnection closed.")

if __name__ == "__main__":
    main()
