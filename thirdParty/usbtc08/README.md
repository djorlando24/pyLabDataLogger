About
===

This repository provides a Python interface for the Pico Technology TC-08 thermocouple logger. A prerequisite is the libusbtc08-1.8 Linux driver installed per the instructions from the Pico Technology website copied below. The header file usbtc08.h will be installed in /opt/picoscope/include/libusbtc08-1.8/. The Python code provides a class for the TC-08 and can be used as logging application. Recorded data is shown in a chart and exported to a logging file in comma-separated format.

Installation
===

Three files are provided in the source folder:

* setup.py (a setup script file for Distutils)

* usbtc08.i (a SWIG interface file for the libusbtc08-1.8 driver)

* usbtc08_logger.py (Python datalogger class and example application)

The following steps install the libusbtc08-1.8 driver, build a Python module using SWIG and a Python package using Distutils. First add the Pico Technology repository:

```bash
$ sudo bash -c 'echo "deb http://labs.picotech.com/debian/ picoscope main" >/etc/apt/sources.list.d/picoscope.list'
```

Import the public key:

```bash
$ wget -O - http://labs.picotech.com/debian/dists/picoscope/Release.gpg.key | sudo apt-key add -
```

Update the package manager cache:

```bash
$ sudo apt-get update
```

Install the Linux driver for USB TC-08 devices:

```bash
$ sudo apt-get install libusbtc08
```

Build the Python module using SWIG:

```bash
$ cd usbtc08/source/
$ swig -python usbtc08.i
```

Build the Python package using Distutils:

```bash
$ python setup.py build_ext --inplace
```

Example Usage
===

Edit the file usbtc08_logger.py to configure the thermocouple types and label the channels. These changes are made to the CHANNEL_CONFIG and CHANNEL_NAME dictionaries. An example is given below, where five K-type thermocouples are used and three disabled are channels. Do not set the cold-junction channel to anything other than 'C' or it raise an error reading the data in streaming mode.

```
CHANNEL_CONFIG = {
    usbtc08.USBTC08_CHANNEL_CJC: 'C', # Needs to be 'C'.
    usbtc08.USBTC08_CHANNEL_1: 'K',
    usbtc08.USBTC08_CHANNEL_2: 'K',
    usbtc08.USBTC08_CHANNEL_3: 'K',
    usbtc08.USBTC08_CHANNEL_4: 'K',
    usbtc08.USBTC08_CHANNEL_5: 'K',
    usbtc08.USBTC08_CHANNEL_6: ' ',
    usbtc08.USBTC08_CHANNEL_7: ' ',
    usbtc08.USBTC08_CHANNEL_8: ' '}
```

```
CHANNEL_NAME = {
    usbtc08.USBTC08_CHANNEL_CJC: 'Cold-junction',
    usbtc08.USBTC08_CHANNEL_1: 'Front',
    usbtc08.USBTC08_CHANNEL_2: 'Rear',
    usbtc08.USBTC08_CHANNEL_3: 'Left',
    usbtc08.USBTC08_CHANNEL_4: 'Right',
    usbtc08.USBTC08_CHANNEL_5: 'Ambient',
    usbtc08.USBTC08_CHANNEL_6: 'Channel 6',
    usbtc08.USBTC08_CHANNEL_7: 'Channel 7',
    usbtc08.USBTC08_CHANNEL_8: 'Channel 8'}
```

The preferred unit is set to the global variable UNIT.

```
UNIT = usbtc08.USBTC08_UNITS_CENTIGRADE
     # usbtc08.USBTC08_UNITS_FAHRENHEIT
     # usbtc08.USBTC08_UNITS_KELVIN
     # usbtc08.USBTC08_UNITS_RANKINE
```

Other settings to consider are the (relative) folder for writing the logging files, the local mains frequency for the filter setting, the use of deskewed data and the output of debug information to the terminal.

```
LOGDIR = 'logs/'
MAINS = 50
DESKEW = True
DEBUG = False
```

Connect the TC-08 to the PC and start a logging session:
```bash
$ python usbtc08_logger.py log
```

Optionally, specify the duration (in seconds) of the logging session and the sample interval in milliseconds:
```bash
$ python usbtc08_logger.py log 60 1500
```

Links
===

[Pico Technology TC-08 thermocouple data logger](https://www.picotech.com/data-logger/tc-08/thermocouple-data-logger)

Status
==

First commit of a working version has been pushed to the repository. See [Issues](https://github.com/bankrasrg/usbtc08/issues) for changes/improvements that are still due.
