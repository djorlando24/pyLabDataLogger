#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
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

    See README.md for further information
"""

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.0.1"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018 LTRAC"


from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy

long_description = """Laboratory datalogging for USB and Serial devices"""

setup(name="pyLabDataLogger",
      version="0.0.1",
      description="Laboratory datalogging for USB and Serial devices.",
      author="Daniel Duke",
      author_email="daniel.duke@monash.edu",
      license="GPL-3.0+",
      long_description=long_description,
      packages=['pyLabDataLogger','pyLabDataLogger.device'],
      package_dir={'pyLabDataLogger': 'src'},
      url='daniel-duke.net',
      include_dirs=[numpy.get_include()]
)
