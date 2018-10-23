# pyLabDataLogger
Laboratory datalogging for USB and Serial devices

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 20/10/2018
        __   ____________    ___    ______    
       / /  /_  ____ __  \  /   |  / ____/    
      / /    / /   / /_/ / / /| | / /         
     / /___ / /   / _, _/ / ___ |/ /_________ 
    /_____//_/   /_/ |__\/_/  |_|\__________/ 

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    This software searches for sensors and data acquisition devices
    over a range of communication protocols and logs them to a local file.
    
    Supported hardware confirmed working includes:
	- Sigrok devices
           confirmed working: Tenma 72-7730A multimeter, 72-7712 Thermometer,
           USBee/LHT00SU1 ADC & logic analyser via fx2lafw driver
    - Tenma 72-2710 USB programmable bench power supply
    - Omega IR-USB thermometer 
	- OHAUS digital lab scales via RS232
	- Microcontrollers using FTDI or CP2102 serial over USB chips
           that push strings with format "VARNAME=VALUE, VARNAME=..."
           (i.e. Arduinos, RS-232 and RS-485 to serial adapters)
        - pyAPT devices (ie Thorlabs translation stages)
    - Picolog USB-TC-08 thermocouple logger
    - Adafruit ADS1x15 i2c-bus 12-bit ADCs (on raspberry pi, beaglebone, etc)
    - CENTER humidity meters
    - USB audio capture devices via ALSA (on Linux)
    
    Soon to be supported hardware:
        - SPI bus devices (i.e. MPL11A1 barometer)
        - I2C bus devices (ie time of flight sensors)
        - GPIO ports (i.e. raspberry pi gpio as TTL inputs)
        - Pico RS-232 TC-08 thermocouple logger
        - PicoScope headless oscilloscopes
        - Measurement Computing devices via mcc-libusb
        - NI-VISA type devices, including
		- Thorlabs PM16-120 power meter
		- NI USB DAQ boards ie 6212-series
        - Agilent 33220A waveform generator via USB or GPIB

    Notes:
	    - Support for Tenma thermometers and multimeters via sigrok's UNI-T drivers
          using the UNI-T D04 USB to serial cables with the WCH.CN ships can require
          a bus reset on Linux before they'll work. To get around this
          you can run scripts/reset-WCH.CN.sh. These devices also have generic USB-to
          -serial adapters than can easily be confused. It may be necessary to specify
          the driver manually when the device is detected.
