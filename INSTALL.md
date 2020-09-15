# INSTALLATION INSTRUCTIONS

Most of the external libraries pyLabDataLogger needs to run specific devices do not need to be installed unless required. pyLabDataLogger will throw an error at you if you need one of these libraries. Details on how to get them are listed below. Before you install, please read below to ensure the modules that are mandatory have been installed, so that the build does not fail.

## Required system libraries to install before building

- hidapi development packages, available on Linux through package manager (apt-get install hidapi-dev) and on MacOS through Homebrew (brew install hidapi).

- libusb headers (libusb-1.0.0 and libusb-1.0.0-dev on Debian/Ubuntu)

- A C++ compiler and standard C++ libraries

- Cython

- python2 and/or python3 development headers

## Required Python modules

pyLabDataLogger depends on the following modules. Those which require legacy versions or are hard to find have been stored in the thirdParty directory.
Use pip, easy_install, apt, etc. to install these.

- numpy

- matplotlib

- cython

- natsort

- tqdm

- termcolor

- re

- subprocess

- glob

- pyusb (for USB device support. Access via pip or pypi/easy_install)

- pylibftdi

- libscrc

- gi-cairo

## building on Linux

The software has been tested extensively on Ubuntu and Debian Linux. 
You'll need to install software from package repository (ie apt or dpkg or yum).
See below sections as to what modules are needed for which drivers.

To install without superuser privileges :

	python setup.py install --user

To install as root, which you may need to do on raspberry Pis etc:

	sudo python setup.py install

## building on MacOS

To compile the mcclibusb drivers, you need libusb installed. On MacOS you can get this
from Homebrew. Once you've done "brew install libusb" you may then need to tell python
where the headers are. On my machine, I used:

    CFLAGS="-I/usr/local/Cellar/libusb/1.0.22/include" python setup.py install --user

## Optional Python modules

From here on, all these modules are optional. They only need to be installed for specific hardware.

### Optional Python modules bundled in thirdParty

- For *Pico USB TC-08*, the usbtc08 python module is required. See thirdParty/usbtc08

- *Measurement Computing* devices require libmccusb, see thirdParty/mcc-libusb
  (you will need to run "make libmccusb.so" in there to build the shared library)

- For *Thorlabs translation stages*, pyAPT for Linux:
  Use the python2 modified version in thirdParty directory, or download from https://gitlab.com/weinshec/pyAPT.git

### Optional Python modules you can obtain from a package manager

- For I2C devices, you will need smbus module:
  and driver specific modules i.e. Adafruit_ADS1x15

- For VISA over TCP/IP for networked devices, pyvisa-py module is required
  Install by 'pip install pyvisa-py' and check installed options with
  'python -m visa info'

- For TC-08 RS-232 serial support, install the thermocouples_reference
  module which provides conversion of thermocouple voltage to temperature.

### Optional Python modules you will need to download and build manually

- for Picoscope devices, install pico-python
  https://github.com/colinoflynn/pico-python

- For Agilent 33220A, usbtmc driver is required.
  See thirdParty/usbtmc or download yourself from https://github.com/python-ivi/python-usbtmc

- For ALSA audio devices, pyalsaaudio
  https://github.com/larsimmisch/pyalsaaudio.git

- For Video4Linux support, v4l2capture module
  https://pypi.org/project/v4l2capture/

- For Picoscope devices, picopython
  https://github.com/colinoflynn/pico-python.git

- For webcam support, OpenCV
  (check your package manager such as apt/pip or use Homebrew on MacOS)

- For CSI camera interface support, libcamera
  see http://libcamera.org/getting-started.html for more information
  libcamera requires a number of additional libraries;
    - libudev-dev libboost-dev libgnutls28-dev openssl libtiff5-dev meson qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5
  There is a test program in tests/test_picamera.py that will confirm libcamera is installed and working.

## Optional non-Python dependencies

- Any generic USB serial port drivers that your system does not have. By default Linux has most standard serial to USB device drivers in the kernel. MacOS and Windows may require FTDI, CP2102, etc. driver packages. These should come with the hardware and are also available online.

- *sigrok*
  You will need to build from source code to get support for the latest devices.
  The version supplied with Ubuntu LTS for example is way out of date and is missing many drivers.
  see https://sigrok.org/wiki/Downloads

    - I found the versions shipped with Ubuntu didn't support all my hardware. 
      Sigrok depends on the following linux packages:
          libftdi, libusb, doxygen, swig, glibmm, python-gobject, python-gi-dev

    - sigrok-firmware-fx2lafw for USBee ADCs, with udev rules installed to avoid
      need for root (see https://sigrok.org/wiki/Fx2lafw)

- for audio devices, ALSA and asound2lib (with asound2lib-dev sources)

- For Video4Linux devices, the v4l2 kernel modules must be installed. These tend to come by default, but can be installed with the system package manager.
    
- For Pico devices, the open source Pico libraries need to be installed.
  These are available from an apt repository for easy installation on Ubuntu.
  see https://www.picotech.com

- For Measurement Computing devices, mcclibusb
  see https://github.com/chrismerck/mcc-libusb.git

- For Video4Linux2 capture devices, you will need the v4l kernel drivers (usually installed by default on most Linux distros).
  To build python's v4l2capture you will need the v4l2 headers (apt-get install libv4l-dev for example)
  You may also need specific device drivers for some USB capture cards (see Hardware.md)

## System configuration notes

- You need to be able to write and read hardware serial ports. On linux, run:
    sudo usermod -a -G dialout $USER

- On Linux, you may need to be root to access USB hardware. You can overcome this by adding udev rules.
  To do this, as root create a file in /etc/udev/rules.d/ and add a line like:
  SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="0957", ATTRS{idProduct}=="1755", GROUP="usbtmc", MODE="0660"
  Then save the file, and as root run: udevadm control --reload-rules && udevadm trigger
  You will also need to add yourself to the group usbtmc: sudo groupadd usbtmc && sudo usermod -a -G usbtmc userName

- *Center 310* hygrometer support is built-in, there are some test utilities in thirdParty/C310
