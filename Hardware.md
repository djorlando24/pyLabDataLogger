# Hardware setup instructions

Most hardware is designed to work with the default factory settings.
Some devices will require special user setup/configuration to be in a mode that makes them compatible with pyLabDataLogger.
Some devices also require manual configuration in the runtime script because they can't be autodetected (mainly, non-USB devices and devices that use a generic USB-to-Serial adapter that can't be uniquely identified).
Those special configurations are explained below.

## Omega iSeries Process Controllers
Using RS-485 comms, the iSeries process controllers need to be set in the following mode. How to do this is explained in the manual.
- RS485 mode
- 9600 baud
- 7 data bits
- 1 stop bit
- odd parity
- command mode (not continuous)
- echo on
- bus address 001 (presently only 1 device per RS485 bus is supported, but it's easy to add more in future).

## Tenma thermometer and multimeters via Sigrok driver
Support for Tenma thermometers and multimeters via sigrok's UNI-T drivers using the UNI-T D04 USB to serial cables with the WCH.CN ships can require a bus reset on Linux before they'll work. To get around this you can run scripts/reset-WCH.CN.sh. 

The generic HID serial adapters are easily confused as their VID/PID are the same. Information that might be useful to identify them doesn't always read the same on every machine (MacOS sees they have unique bcdDevice strings but Linux kernel doesn't).

You will need to tell pyLabDataLogger which of these devices is found at a given USB device address:

		Code block
