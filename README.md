# pyLabDataLogger
Laboratory datalogging for USB and Serial devices

## Caution, this software is in Beta and may not work reliably yet!
Try scripts/test_usb_devices.py to poll compatible USB devices.

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 15/03/2019
        __   ____________    ___    ______    
       / /  /_  ____ __  \  /   |  / ____/    
      / /    / /   / /_/ / / /| | / /         
     / /___ / /   / _, _/ / ___ |/ /_________ 
    /_____//_/   /_/ |__\/_/  |_|\__________/ 

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    This software searches for sensors and data acquisition devices
    over a range of communication protocols and logs them to a local file.

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

- NI-VISA over Ethernet devices that use SCPI command set
    - Rigol DG1000Z series delay generators
    - Rigol DS1000Z series oscilloscopes
    - Agilent 33220A waveform generator

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
    - Fluke 568 IR thermometer
    
- USB Devices using Linux kernel drivers (not supported on MacOS)
    - USB audio capture devices via ALSA
    - Video4Linux capture interfaces 

- RS-232 Serial devices via Serial-to-USB adapters
    - Tenma 72-2710 USB programmable bench power supply
    - Pico RS-232 TC-08 thermocouple logger
    - Omega iSeries temperature process controllers, via RS-485 or RS-232
    - CENTER 310 humidity meter
    - OHAUS digital lab scales via RS232-to-USB
    - Extech SD700 Barometric pressure/humidity/temperature datalogger

- Single board computer (Raspberry Pi, Beaglebone) I2C, SPI & GPIO
    - Adafruit ADS1x15 12-bit ADCs via I2C
    - Adafruit BMP085/BMP150 barometer/altimeter via I2C
    - Raspberry Pi low speed GPIO

## Soon to be supported hardware

- more I2C bus devices (ie time of flight sensors)
- PicoScope headless oscilloscopes
- NI-VISA over USB devices, such as
    - Thorlabs PM16-120 power meter
    - NI USB DAQ boards ie 6212-series

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
