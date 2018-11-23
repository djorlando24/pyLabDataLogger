# INSTALLATION INSTRUCTIONS

## Required python modules

pyLabDataLogger depends on the following non-core python packages.
Those which require legacy versions or are hard to find have been stored in the thirdParty directory.

### Python modules bundled in thirdParty

- For *Pico USB TC-08*, the usbtc08 python module is required. See thirdParty/usbtc08

- *Measurement Computing* devices require libmccusb, see thirdParty/mcc-libusb
  (you will need to run "make libmccusb.so" in there to build the shared library)

- For *Thorlabs translation stages*, pyAPT for Linux:
  Use the python2 modified version in thirdParty directory, or download from https://gitlab.com/weinshec/pyAPT.git

- *Center 310* hygrometer support is built-in, there are some test utilities in thirdParty/C310

- *sigrok*
  You will need to build from source code to get support for the latest devices.
  see https://sigrok.org/wiki/Downloads

    - I found the versions shipped with Ubuntu didn't support all my hardware. Sigrok depends on the following linux packages:
        libftdi, libusb, doxygen, swig, glibmm, python-gobject, python-gi-dev

    - sigrok-firmware-fx2lafw for USBee ADCs, with udev rules installed to avoid
      need for root (see https://sigrok.org/wiki/Fx2lafw)

### External python modules you must install yourself

- numpy (usually comes bundled with Python)

- pyusb (for USB device support. Access via pip or pypi/easy_install)

- For I2C devices, you will need smbus module:
  and driver specific modules i.e. Adafruit_ADS1x15

- for Picoscope devices, install pico-python
  https://github.com/colinoflynn/pico-python

- For Agilent 33220A, usbtmc driver is required.
  See thirdParty/usbtmc or download yourself from https://github.com/python-ivi/python-usbtmc

- For ALSA audio devices, pyalsaaudio
  https://github.com/larsimmisch/pyalsaaudio.git

## Non-Python dependencies

pyLabDataLogger also requires the following external software:

- hidapi development packages, available on Linux through package manager (apt-get install hidapi-dev) and on MacOS through Homebrew (brew install hidapi).

- python2 and python3 development headers

- Any generic USB serial port drivers that your system does not have. By default Linux has most standard serial to USB device drivers in the kernel. MacOS and Windows may require FTDI, CP2102, etc. driver packages. These should come with the hardware and are also available online.

- for audio devices, ALSA and asound2lib (with asound2lib-dev sources)
    
- For Pico devices, the open source Pico libraries need to be installed.
  see https://www.picotech.com

- For Measurement Computing devices, mcclibusb
  see https://github.com/chrismerck/mcc-libusb.git

## System configuration notes

- You need to be able to write and read hardware serial ports. On linux, run:
    sudo usermod -a -G dialout $USER

- On Linux, you may need to be root to access USB hardware. You can overcome this by adding udev rules.
  To do this, as root create a file in /etc/udev/rules.d/ and add a line like:
  SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="0957", ATTRS{idProduct}=="1755", GROUP="usbtmc", MODE="0660"
  Then save the file, and as root run: udevadm control --reload-rules && udevadm trigger
  You will also need to add yourself to the group usbtmc: sudo groupadd usbtmc && sudo usermod -a -G usbtmc userName

## Install procedure

- Go to the pyLabDataLogger directory and run
  python setup.py install --user

  or to install system-wide with superuser, do:
  sudo python setup.py install

  Note that missing dependencies will not be picked up at install time. These will flag
  as ImportError throws or warning messages at run-time.
