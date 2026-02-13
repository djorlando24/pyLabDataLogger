#/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Laboratory datalogging for USB and Serial devices

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 13/06/25

    Multiphase Flow Laboratory
    Monash University, Australia

    This software searches for sensors and data acquisition devices
    over a range of communication protocols and logs them to a local file.
    Supported interfaces include:
    - USB via sigrok - i.e. many multimeters, logic analyzers and oscilloscopes
    - USB serial ports (i.e. Arduino via FTDI, RS-232 and RS-485 to serial adapters)
    - USB devices via other proprietary drivers
    - NI-VISA ethernet devices
    - SPI bus devices
    - I2C bus devices
    - GPIO ports

    See README.md for further information
"""

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="1.4.0"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018-2025 D.Duke"


#from distutils.core import setup
#from distutils.extension import Extension
from setuptools import setup, Extension

from Cython.Build import cythonize
import numpy, sys

long_description = """Easy data logging from USB, Serial and Network devices"""


# Build cython modules
cython_modules = [
]

# Build C libraries that interface to hardware
c_libraries = [
]

# Add platform-dependent C libraries
if 'linux' in sys.platform:
    c_libraries.append(Extension("libmcp3424", sources = ["src/device/i2c/mcp3424.c"]))
    c_libraries.append(Extension("libmccusb1608G", sources = ["src/mcclibusb/usb-1608G.c"]))

# Add platform-dependent include directories (ie Homebrew on MacOS)
include_dirs=[numpy.get_include(), '/opt/homebrew/include']
if 'darwin' in sys.platform:
    include_dirs.append('/usr/local/include')

try:
    from distutils.msvccompiler import get_build_version as get_build_msvc_version
except ImportError:
    def get_build_msvc_version():
        return None

setup(name="pyLabDataLogger",
      version="1.4",
      description="Laboratory datalogging for USB and Serial devices.",
      author="Daniel Duke",
      author_email="daniel.duke@monash.edu",
      license="GPL-3.0+",
      long_description=long_description,
      packages=['pyLabDataLogger','pyLabDataLogger.logger','pyLabDataLogger.device','pyLabDataLogger.device.i2c','pyLabDataLogger.mcclibusb'],
      package_dir={'pyLabDataLogger': 'src'},
      url='daniel-duke.net',
      ext_modules=cythonize(cython_modules) + c_libraries,
      include_dirs=include_dirs
)
