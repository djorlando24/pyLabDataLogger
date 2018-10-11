# pyLabDataLogger
Laboratory datalogging for USB and Serial devices

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 11/10/2018
        __   ____________    ___    ______    
       / /  /_  ____ __  \  /   |  / ____/    
      / /    / /   / /_/ / / /| | / /         
     / /___ / /   / _, _/ / ___ |/ /_________ 
    /_____//_/   /_/ |__\/_/  |_|\__________/ 

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    This software searches for sensors and data acquisition devices
    over a range of communication protocols and logs them to a local file.
    Supported interfaces include:
	- USB via sigrok - i.e. many multimeters, logic analyzers and oscilloscopes
        - USB serial ports (i.e. Arduino via FTDI, RS-232 and RS-485 to serial adapters)
        - USB via other proprietary drivers
        - SPI bus devices
        - I2C bus devices
        - GPIO ports


    Currently supported hardware:
