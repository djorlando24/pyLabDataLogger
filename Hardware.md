# Hardware setup instructions

Most hardware is designed to work with the default factory settings.
Some devices will require special user setup/configuration to be in a mode that makes them compatible with pyLabDataLogger.
Some devices also require manual configuration in the runtime script because they can't be autodetected (mainly, non-USB devices and devices that use a generic USB-to-Serial adapter that can't be uniquely identified).
Those special configurations are explained below.

## Omega iSeries Process Controllers
The iSeries process controllers need to be set in the following mode. How to do this is explained in the manual.
- 9600 baud
- 7 data bits
- 1 stop bit
- odd parity
- command mode (not continuous)
- For RS485, echo on. For RS232, echo off.
- bus address 001 (in future this could be variable to support >1 controller on an RS-485 bus).

## Tenma thermometer and multimeters via Sigrok driver
- Support for Tenma thermometers and multimeters via sigrok's UNI-T drivers using the UNI-T D04 USB to serial cables with the WCH.CN ships can require a bus reset on Linux before they'll work. To get around this you can run scripts/reset-WCH.CN.sh. 

- Modern MacOS doesn't allow userspace drivers to access USB HID devices for security
  reasons, so devices that use USB HID like sigrok's UNI-T drivers don't work.

- The generic HID serial adapters are easily confused as their VID/PID are the same. Information that might be useful to identify them doesn't always read the same on every machine (MacOS sees they have unique bcdDevice strings but Linux kernel doesn't). If pyLabDataLogger sees one of these generic HID adapters it will ask you what device it corresponds to, if not sure. You can enforce selection by specifying the bus & address variables of the device. Beware that these change every time you unplug & plug the USB device.

- In order to get these Tenma thermometers and multimeters to work they have to be put into SEND mode (there will be a button for it on the front panel). You will see "USB" or "SEND" on the LCD display.

## Thorlabs TSP01
Make sure the usbtmc rules are added in /etc/udev/rules.d as per INSTALL.md
If the device won't communicate, unplug & replug it.

## Rigol DS-series oscilloscopes
The Rigol DS scopes are working over USB via the sigrok driver, which seems to handle the non standard SCPI frame fsormat that usbtmc can't.

Rigol DS scopes also work via their ethernet connection using the pyvisa driver. Get the resource string by browsing to the device's IP address in a web browser.

The scope needs to be set up and armed before the acquisition is started. Single shot mode may not work, I find best results arming it in Auto mode and letting sigrok acquire what's most recently on the screen. If things go wrong you can set 'debugMode':True in the kwargs to the device driver and see what is happening behind the scenes.

## GPIB oscilloscopes
Oscilloscopes using the GPIB-USB adapter (http://dangerousprototypes.com/blog/2014/01/13/open-source-hardware-gpib-usb-adapter/) should be set to GPIB bus address 1 by default. The code assumes there's only one device on the bus unless you specify 'gpib-address' when generating the device object.

# I2C Devices
I2C devices that use Adafruit libraries rely on deprecated python libraries which have been copied into thirdParty in case
the old repositories on Github go away. These devices have been tested on Raspberry pi, but should work on Beaglebones as well.
