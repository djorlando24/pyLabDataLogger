# pyLabDataLogger
Laboratory datalogging for USB and Serial devices

## Caution, this software is in Beta and may not work reliably yet!

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 26/11/2018
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
       confirmed working: Tenma 72-7730A multimeter, 72-7712 Thermometer,
       USBee/LHT00SU1 ADC & logic analyser via fx2lafw driver

- USBTMC devices that use SCPI command set
       confirmed working: Agilent 33220A waveform generator (USB),
       Rigol DS series oscilloscopes.

- Microcontrollers using FTDI or CP2102 serial over USB chips
       that push strings with format "VARNAME=VALUE, VARNAME=..."
       (i.e. Arduinos, RS-232 and RS-485 to serial adapters)
    - pyAPT devices (ie Thorlabs translation stages)

- Measurement Computing devices via mcc-libusb
    - MCC-USB-1608G confirmed working

- Devices with specialised drivers
    - Picolog USB-TC-08 thermocouple logger
    - USB audio capture devices via ALSA (on Linux)
    - Tenma 72-2710 USB programmable bench power supply
    - Omega IR-USB thermometer 
    - Omega iSeries temperature process controllers, via RS-485
    - CENTER 310 humidity meter
    - OHAUS digital lab scales via RS232-to-USB

- Single board computer (Raspberry Pi, Beaglebone) I2C, SPI & GPIO
    - Adafruit ADS1x15 12-bit ADCs via I2C


## Soon to be supported hardware
- Thorlabs TSP01 temperature & humidity sensor
- more SPI bus devices (i.e. MPL11A1 barometer)
- more I2C bus devices (ie time of flight sensors)
- Raspberry PI GPIO pins
- Pico RS-232 TC-08 thermocouple logger
- PicoScope headless oscilloscopes
- NI-VISA type devices, including
    - Thorlabs PM16-120 power meter
    - NI USB DAQ boards ie 6212-series

## Notes
- Most devices require additional python modules or third party open source
  drivers. See INSTALL notes.

- Support for Tenma thermometers and multimeters via sigrok's UNI-T drivers
  using the UNI-T D04 USB to serial cables with the WCH.CN ships can require
  a bus reset on Linux before they'll work. To get around this
  you can run scripts/reset-WCH.CN.sh. These devices also have generic USB-to
  -serial adapters than can easily be confused. It may be necessary to specify
  the driver manually when the device is detected.

- While Rigol scopes are supported by both sigrok and usbtmc, they are not fully
  compilant with the standards and connectivity issues are common. These still need to be fixed.

See Hardware.md for more detailed information.
