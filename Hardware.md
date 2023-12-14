# Hardware setup instructions

Most hardware is designed to work with the default factory settings.

If you want to change the baud rate, etc, you can over-ride the default settings when initialising the PyLabDataLogger device class instance.

Some devices will require special user setup/configuration to be in a mode that makes them compatible with pyLabDataLogger.

Some devices also require manual configuration in the runtime script because they can't be autodetected (mainly, non-USB devices and devices that use a generic USB-to-Serial adapter that can't be uniquely identified).

Those special configurations are explained below.

# USB Devices

## LHT00SU1 logic analyser

- This unit works via sigrok and must be flashed with fx2lafw firmware to work.

- If you see "Unable to communicate with LHT00SU1 logic analyzer" error, try first `./tests/test_LHT00SU1.sh` a few times. 

## Tenma thermometer and multimeters 
- In order to get the devices work they might have to be put into SEND mode (there will be a button for it on the front panel). You will see "USB" or "SEND" on the LCD display.

- *Tenma 72-771x and UNI-T UT32x thermocouple readers* now have a custom HID driver that is more reliable than using sigrok. If it does not detect, run `python3 tests/test_tenma72-7712.py` first.

- The generic HID serial adapters are easily confused as their VID/PID are the same. Information that might be useful to identify them doesn't always read the same on every machine (MacOS sees they have unique bcdDevice strings but Linux kernel doesn't). If pyLabDataLogger sees one of these generic HID adapters it will ask you what device it corresponds to, if not sure. You can enforce selection by specifying the bus & address variables of the device. Beware that these change every time you unplug & plug the USB device.

- Did you get an error `USBError: [Errno 13] Access denied (insufficient permissions)`? Read below to see how to fix it.

- macOS doesn't allow userspace drivers to access USB HID devices for security
  reasons, so devices that use USB HID like sigrok's UNI-T drivers don't work at all right now. Sorry! You might want to run a Linux virtual machine.

- On Linux, you may need to modify your udev rules to get user-level access to the WCH.CN chips used in the Tenma and Uni-T thermometers and multimeters.

    - If sigrok is installed, you may simply need to modify line 30 of `/etc/udev/rules.d/61-libsigrok-uaccess.rules`  to make it `ENV{ID_SIGROK}=="1", TAG+="uaccess", MODE="0666"`.
    
    - if sigrok is not installed, create a new file in `/etc/udev/rules.d` and add `SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="e008", MODE="0666"`.
    
    - Once modified, reload the rules with `sudo udevadm control -R` and `sudo udevadm trigger` 
    
    - If your user still lacks permissions, do `sudo usermod -a -G dialout $(whoami)` and then log out and in again.

- On Linux, if these devices sometimes fail to respond until they get unplugged & replugged, they might require a bus reset to avoid the physical unplugging. To get around this you can run `scripts/reset-WCH.CN.sh`. 

## Omega Smart Probes
Support for the Omega IF-001 USB Serial to MODBUS interface adapter is included. It's also possible to use I2C hardware (for example on the Raspberry Pi) with a custom cable, but this isn't supported in code yet.  The USB interface uses the cdc_acm driver in Linux, and you may need permissions to access the /dev/ttyACM0 or similar device without being root. You can do this by copying thirdParty/99-omegaIF001.rules with superuser priveliges into /etc/udev/rules.d and issuing 

    udevadm control --reload-rules

Then unplug and replug the device.

## DataQ DI-14x USB interfaces
These devices have a custom VID and PID but are actually just FTDI FT232R serial interfaces. To make these work on Linux, you can copy thirdParty/99-dataq.rules to /etc/udev/rules.d and make the change effective with:

    udevadm control --reload-rules

Then unplug and replug the device.

## Thorlabs TSP01 and PM16 devices
Make sure the usbtmc rules are added in /etc/udev/rules.d as per INSTALL.md
If the device won't communicate, unplug & replug it.
you will otherwise need to be a superuser to access the device.

Please note: Thorlabs has updated the TSP01 since this code was written. If your TSP01 has "Rev B" sticker, it won't work.


## Rigol DS-series oscilloscopes
The Rigol DS scopes are working over USB via the sigrok driver, which seems to handle the non standard SCPI frame fsormat that usbtmc can't.

Rigol DS scopes also work via their ethernet connection using the pyvisa driver. Get the resource string by browsing to the device's IP address in a web browser.
python3-pyvisa should be installed. Use 'python3 -m visa info' to check for visa support on your system.

The scope needs to be set up and armed before the acquisition is started. Single shot mode may not work, I find best results arming it in Auto mode and letting sigrok acquire what's most recently on the screen. If things go wrong you can set 'debugMode':True in the kwargs to the device driver and see what is happening behind the scenes.

# Serial Devices

## Omega iSeries Process Controllers
The iSeries process controllers need to be set in the following mode. How to do this is explained in the manual.
- 9600 baud
- 7 data bits
- 1 stop bit
- odd parity
- command mode (not continuous)
- For RS485, echo on. For RS232, echo off.
- bus address 001 (in future this could be variable to support >1 controller on an RS-485 bus).

## Agilent / HP function generators
When using the RS232 interface, a null-modem cable is required and the communication should be set to SCPI, 9600 baud 8N1. These use the pyvisa module.
For newer models with a builtin USB interface, the usbtmc module can be used to automate the communication settings.

## GPIB oscilloscopes
Oscilloscopes using the GPIB-USB adapter (http://dangerousprototypes.com/blog/2014/01/13/open-source-hardware-gpib-usb-adapter/) should be set to GPIB bus address 1 by default. The code assumes there's only one device on the bus unless you specify 'gpib-address' when generating the device object.

A HP 53131A counter can also be supported via GPIB-USB and is at its factory default GPIB address of 3.

## Extech USB-RS232 adapters
The Extech brand USB to RS232 adapters are multifunction and some have a switch to choose between mode 1 & 2. You must select mode 2 for the communications to work.

## AND G-series precision balances
The software assumes default serial port settings of 2400 baud, 7 data bits, even parity, 2 stop bits, no flow control.
You can modify these in the software if you wish.

## Leadshine ES-D508 servomotor controller
The RJ-12 to RS-232 adapter supplied for tuning the ES-D508 servomotor controller can be used to move the motor and poll the encoder to get the current position. The tuning constants may need adjustment depending on choice of motor, which can be determined using the tuning software supplied by the manufacturer.

## Ranger 5000 Load Cell Amplifier
Connect via Serial1. Set communications mode to Net.A (Rinstrum)
Assumes RS232 communications at 19600 baud 8N1, device address 31, 0x02 start byte and 0x03 end byte for messages.
Note that default settings might be for printer mode, and 9600 baud, so will need to check settings if device is powered off for a long time.
Flow control lines on serial port must be disonnected (only RX, TX & GND wires).

## Omron K3HB readout units with FLK1B CompoWay/F RS-232/485 communications
Assumes the default device address of 01 (factory setting).
Assumes the serial comms are at 9600 baud 8N1. The factory default comms mode is 9600 7O2 and this needs to be fixed in the device's menus.
The device doesn't indicate its units of measurement; the scale and offset must be set by the user on the device.

# Video capture devices

## Thorlabs scientific cameras
Download the closed-source (boo!) drivers and SDK from https://www.thorlabs.com/software_pages/viewsoftwarepage.cfm?code=ThorCam
Follow the install directions (which requires manually copying the libraries, installing the python package, and inserting udev rules).

## Webcams
Webcame frame capture requires the OpenCV library. If your webcam is not detected you may need to add its VID and PID to the device table in src/device/usbDevice.py, and specify the 'opencv' driver. Then merge your changes so I can expand the supported deice list!

## Video4Linux capture devices
USB video capture device support depends on v4l2 support. A significant number of PCI and USB capture cards are not supported by Linux, so check https://www.linuxtv.org/downloads/v4l-dvb-apis-new/v4l-drivers/cardlist.html before you buy! Tested devices that work have their USB VID/PID added to usbDevice.py. These include:
- Roxio video capture USB UB315-E ver3 with EMPIA em2860 chip, uses the em28xx driver
- NexTech XC4991 USB video capture with SoMagic chip, uses a custom sm2021 driver, install instructions at https://github.com/Manouchehri/smi2021

To get correct resolution detected for some v4l2 devices, I had to run v4l2-ctl --set-fmt-video=width=720,height=480 then I had to used v4l2ucp to check stream works ok. Those programs should be available through apt or yum, etc.



## Center 310 Hygrometer
*Center 310* hygrometer support via RS-232 is now built-in, there are some test utilities in thirdParty/C310 if you experience problems.

# I2C / IIC devices

Please note that hardware I2C support has only been tested on **Rasberry Pi** so far. I cannot guarantee proper smbus support on other systems.

Adafruit devices use libraries from Adafruit which can be obtained mostly via pip (ie `sudo pip3 install adafruit_foo`). For those that can't use pip you can get a working module via github:
- MPR121 - https://github.com/adafruit/Adafruit_CircuitPython_MPR121

Devices that use 'clock stretching' aren't supported due to RPi <= 4's lack of support for this. However, the Bosch BNO055 has a UART mode (tie pin PS1 to 3.3v; SCA and SCL become a UART). The UART interface works fine with a USB-FTDI chip, the 'bno055' drivers supports this UART communications. To use the BNO055 you'll need the Adafruit module 'adafruit-circuitpython-bno055'. See https://github.com/adafruit/Adafruit_CircuitPython_BNO055 

Any libraries that are no longer available or require older versions are available in ThirdParty directory for convenience.

Notes:
- MCP3424 is based on alxyng's userspace driver at https://github.com/alxyng/mcp3424
- H3LIS331DL driver is based on ControlEverything's script from https://github.com/ControlEverythingCommunity/H3LIS331DL

## Devices that won't work on Raspberry Pi

Devices that use clock stretching usually don't work on the Pi unless you bit-bang the I2C which is not very efficient, and it messes with anything else on the bus. Given this, I have not tried to implement drivers for those devices on purpose. Affected devices I've found so far that we can't support are:
- BNO055 9-axis orientation sensor
- TFMini Lidar Module [ it has a UART interface that could work though! ]

To use the above devices I suggest you connect them to an Arduino (or similar microcontroller with usb) and use the arduinoDevice interface to pull down the data. Then you can use the off-the-shelf Arduino libraries with very little effort. Same applies to any I2C or SPI device that doesn't have a Rasberry Pi smbus driver.

# Can you add support for my device?
I can't test and add support for hardware unless I actually have the equipment in my hands to test it, and the time to do so.
However, you can add support for your own device and then make a merge request to the main branch later.
- If your device is supported by sigrok, OpenCV or video4Linux it's as simple as adding the USB VID and PID to the table in src/device/usbDevice.py
- If your device uses RS-232/RS-485, you can add it as a new subdriver to src/device/serialDevice.py following the examples already there.
- If your device uses SCPI over USB, you can add it as a new subdriver to src/device/usbtmcDevice.py following the examples already there.
- If your device uses VISA over Ethernet or USB, you can add it as a subdriver to src/device/visaDevice.py following the examples already there.
- If your device is a variant of an already supported device (i.e. Thorlabs APT or PM-like) you may be able to add it to the USB table
  in in src/device/usbDevice.py and then edit the specific driver class in src/device to add a subdriver that accepts it.
- For all other cases you can copy src/device/genericDevice.py and use this as a template to add a new driver class (i.e. new low level driver required).
