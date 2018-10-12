# pyLabDataLogger
Laboratory datalogging for USB and Serial devices

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 12/10/2018
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
	- Sigrok devices - i.e. Tenma multimeters, thermometers,
           generic USBee logic analyzers and Rigol oscilloscopes
        - Tenma 72-2710 USB programmable bench power supply
        - Omega IR-USB thermometer 
	- OHAUS digital lab scales via RS232
	- Microcontrollers using FTDI or CP2102 serial over USB chips
           that push strings with format "VARNAME=VALUE, VARNAME=..."
           (i.e. Arduinos, RS-232 and RS-485 to serial adapters)
        - pyAPT devices (ie Thorlabs translation stages)

    Soon to be supported hardware:
        - SPI bus devices (i.e. raspberry pi)
        - I2C bus devices (i.e. raspberry pi)
        - GPIO ports (i.e. raspberry pi)
        - Picolog TC-08 thermocouple logger
        - PicoScope headless oscilloscopes
        - Measurement Computing devices via mcc-libusb
	    - Thorlabs PM120 power meter
    	- CENTER humidity meters
	    - USB audio capture devices (via alsa-record)
        - Agilent 33220A waveform generator via USB or GPIB
