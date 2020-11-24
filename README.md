# pyLabDataLogger
Laboratory datalogging for USB and Serial devices

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 1.0.3
    @date 24/11/2020
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

    This software searches for sensors and data acquisition devices
    over a range of communication protocols and logs them to a local file.

## TLDR

This software is still in early development and cannot be guaranteed to work
reliably. You may need to tinker with src/device/usbDevice.py if your USB
to Serial adapters have different VID/PIDs to mine.

Try scripts/test_usb_devices.py to poll compatible USB devices.

## Supported hardware

- Sigrok devices
     confirmed working:
    - Tenma 72-7730A multimeter
    - Tenma 72-7712 thermometer
    - Rigol DS-series oscilloscopes
    - USBee/LHT00SU1 ADC & logic analyser via fx2lafw driver

- USBTMC devices that use SCPI command set
    - Agilent 33220A waveform generator,
    - Thorlabs TSP01 temperature & humidity logger
    - Thorlabs PM16 series power meters

- NI-VISA over Ethernet devices that use SCPI command set
    - Rigol DG1000Z series delay generators
    - Rigol DS1000Z series oscilloscopes
    - Agilent 33220A waveform generator
    - Envox Experimental Zone EEZ BB3 modular programmable power supply

- Microcontrollers using FTDI or CP2102 serial over USB chips
       that push strings with format "VARNAME=VALUE, VARNAME=..."
       (i.e. Arduinos, RS-232 and RS-485 to serial adapters)

- pyAPT devices (ie Thorlabs K-cube motor drivers)

- Measurement Computing devices via mcc-libusb
    - MCC-USB-1608G confirmed working

- GPIB devices that use the GPIB-USB serial adapter
    - Tektronix TDS220 series oscilloscopes

- USB Devices with custom interfaces/drivers
    - Picolog USB-TC-08 thermocouple logger
    - Omega IR-USB thermometer
    - Omega USB-H 'high speed' pressure transducers 
    - Fluke 568 IR thermometer
    
- USB Devices using Linux kernel drivers (not supported on MacOS)
    - USB audio capture devices via ALSA
    - Video4Linux capture interfaces (i.e. video capture cards, see Hardware.md for details)

- Generic USB webcams supported by OpenCV
    - Note that OpenCV2 can't tell multiple webcams apart, user
      would be asked which is which.

- CSI camera interfaces such as the Raspberry Pi Camera, using libcamera
    - see libcamera.org for information
    
- Thorlabs Scientific Cameras (using Thorlabs SDK and non-free drivers)
    - see https://www.thorlabs.com/software_pages/viewsoftwarepage.cfm?code=ThorCam
    requires Intel 32 or 64 bit processor (Thorlabs only provides precompiled DLLs)

- RS-232 Serial devices via Serial-to-USB adapters. pyLabDataLogger may not be able to auto-identify the USB VID & PID and you might be asked to select from a list of supported devices.
    - Tenma 72-2710 USB programmable bench power supply
    - Pico RS-232 TC-08 thermocouple logger via generic RS-232 adpater
    - CENTER 310 humidity meter via model-specific serial to USB dongle
    - OHAUS digital lab scales via generic RS-232 adapter
    - Extech SD700 Barometric pressure/humidity/temperature datalogger via model-specific serial to USB dongle
      (must set mode switch on dongle to '2')
    - Alicat Scientific M-series mass flow meters via RS232-to-USB dongle
      (default baud rate 19200, default unit ID 'A')
    - Leadshine ES-D508 servomotor controller
    - Metrix MX5060 Bench multimeter (contains an internal generic CP210x Serial-to-USB bridge)
    - Radwag WTB series digital lab balance/scale via RS232-to-USB UART adapter **
    - Ranger 5000 Load Cell Amp via RS232-to-USB adapter **
    - Omega iSeries temperature process controllers, via generic RS-485 or RS-232 adapter **
    - Status SEM1600/B Load Cell Amplifier (contains and internal FTDI Serial-to-USB bridge)
    - Omron K3HB-VLC load cell process controller with FLK1B RS-232/485 comms option board

        ** Double asterisk denotes the need for a TTL-UART type adapter without flow control lines.
           Testing with generic RS-232 to USB adapters indicated that when the PC attempts to take control of the flow control
           lines upon initialising the adapter, the device will cease transmitting and it cannot be restarted without disconnecting the serial cable. The simple solution is to wire up a TTL-to-UART adapter cable to an RS232 adapter, connecting only the RX, TX, VCC and GND lines (leaving the CTS/RTS/DTR lines disconnected).

- Single board computer (Raspberry Pi, Beaglebone) I2C, SPI & GPIO
    - Adafruit ADS1x15 12-bit ADCs via I2C
    - Adafruit BMP085/BMP150 barometer/altimeter via I2C
    - Raspberry Pi low speed GPIO

## Future supported hardware

- more I2C bus devices on the Raspberry Pi

- PicoScope headless oscilloscopes

- NI-VISA devices, such as
    - NI USB DAQ boards ie 6212-series
    - NI PCI card DAQs
    
- Firewire machine vision cameras (libdc1394)
  [https://damien.douxchamps.net/ieee1394/cameras/]

## Notes
- Most devices require additional python modules or third party open source
  drivers. See INSTALL notes.

- Support for Tenma thermometers and multimeters via sigrok's UNI-T drivers
  using the UNI-T D04 USB to serial cables with the WCH.CN chips can require
  a bus reset on Linux before they'll work. To get around this
  you can run scripts/reset-WCH.CN.sh. These devices also have generic USB-to
  -serial adapters than can easily be confused. It may be necessary to specify
  the driver manually when the device is detected.

- MacOS doesn't allow userspace drivers to access USB HID devices for security
  reasons, so devices that use USB HID like sigrok's UNI-T drivers don't work.

See Hardware.md for more detailed information.
