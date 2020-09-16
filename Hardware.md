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

## Thorlabs TSP01 and PM16 devices
Make sure the usbtmc rules are added in /etc/udev/rules.d as per INSTALL.md
If the device won't communicate, unplug & replug it.
you will otherwise need to be a superuser to access the device.

## Thorlabs scientific cameras
Download the closed-source (boo!) drivers and SDK from https://www.thorlabs.com/software_pages/viewsoftwarepage.cfm?code=ThorCam
Follow the install directions (which requires manually copying the libraries, installing the python package, and inserting udev rules).

## Rigol DS-series oscilloscopes
The Rigol DS scopes are working over USB via the sigrok driver, which seems to handle the non standard SCPI frame fsormat that usbtmc can't.

Rigol DS scopes also work via their ethernet connection using the pyvisa driver. Get the resource string by browsing to the device's IP address in a web browser.

The scope needs to be set up and armed before the acquisition is started. Single shot mode may not work, I find best results arming it in Auto mode and letting sigrok acquire what's most recently on the screen. If things go wrong you can set 'debugMode':True in the kwargs to the device driver and see what is happening behind the scenes.

## GPIB oscilloscopes
Oscilloscopes using the GPIB-USB adapter (http://dangerousprototypes.com/blog/2014/01/13/open-source-hardware-gpib-usb-adapter/) should be set to GPIB bus address 1 by default. The code assumes there's only one device on the bus unless you specify 'gpib-address' when generating the device object.

## Extech USB-RS232 adapters
The Extech brand USB to RS232 adapters are multifunction and some have a switch to choose between mode 1 & 2. You must select mode 2 for the communications to work.

## Leadshine ES-D508 servomotor controller
The RJ-12 to RS-232 adapter supplied for tuning the ES-D508 servomotor controller can be used to move the motor and poll the encoder to get the current position. The tuning constants may need adjustment depending on choice of motor, which can be determined using the tuning software supplied by the manufacturer.

## I2C Devices
I2C devices that use Adafruit libraries rely on deprecated python libraries which have been copied into thirdParty in case
the old repositories on Github go away. These devices have been tested on Raspberry pi, but should work on Beaglebones as well.

## Webcams
Webcame frame capture requires the OpenCV library. If your webcam is not detected you may need to add its VID and PID to the device table in src/device/usbDevice.py, and specify the 'opencv' driver. Then merge your changes so I can expand the supported deice list!

## Video4Linux capture devices
USB video capture device support depends on v4l2 support. A significant number of PCI and USB capture cards are not supported by Linux, so check https://www.linuxtv.org/downloads/v4l-dvb-apis-new/v4l-drivers/cardlist.html before you buy! Tested devices that work have their USB VID/PID added to usbDevice.py. These include:
- Roxio video capture USB UB315-E ver3 with EMPIA em2860 chip, uses the em28xx driver
- NexTech XC4991 USB video capture with SoMagic chip, uses a custom sm2021 driver, install instructions at https://github.com/Manouchehri/smi2021

To get correct resolution detected for some v4l2 devices, I had to run v4l2-ctl --set-fmt-video=width=720,height=480 then I had to used v4l2ucp to check stream works ok. Those programs should be available through apt or yum, etc.


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
