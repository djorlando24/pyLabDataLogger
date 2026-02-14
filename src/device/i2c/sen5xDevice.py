#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Adafruit BMP Barometric Pressure Sensor device class
    Compatible with BMP085 and BMP150 
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 13/06/25

    Multiphase Flow Laboratory
    Monash University, Australia
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from .i2cDevice import *
from ..device import pyLabDataLoggerIOError
import datetime, time
import numpy as np
from termcolor import cprint

try:
    from sensirion_i2c_driver import I2cConnection
    from sensirion_i2c_sen5x import Sen5xI2cDevice
    import i2cdriver
except ImportError:
    cprint( "Error, could not load sensirion_i2c_driver, sensirion_i2c_sen5x or i2cdriver library", 'red', attrs=['bold'])

########################################################################################################################
class i2cdriver_interface(object):
    """ class that provides sensirion_i2c_driver.I2cConnection an interface to i2cdriver. 
        Maps one API to the Other. """
    
    API_VERSION = 1  #: API version (accessed by I2cConnection)

    # Status codes
    STATUS_OK = 0  #: Status code for "transceive operation succeeded".
    STATUS_CHANNEL_DISABLED = 1  #: Status code for "channel disabled error".
    STATUS_NACK = 2  #: Status code for "not acknowledged error".
    STATUS_TIMEOUT = 3  #: Status code for "timeout error".
    STATUS_UNSPECIFIED_ERROR = 4  #: Status code for "unspecified error".
    
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self,exc_type, exc_val, exc_tb):
        self.close()
    
    def __init__(self,device_file="/dev/ttyUSB0"):
        self.port=device_file
        self.open()

    def description(self):
        return "i2cdriver interface"
    
    def channel_count(self):
        return None
   
    def transceive(self, slave_address, tx_data, rx_length, read_delay, timeout):
        assert type(slave_address) is int
        assert (tx_data is None) or (type(tx_data) is bytes)
        assert (rx_length is None) or (type(rx_length) is int)
        assert type(read_delay) in [float, int]
        assert type(timeout) in [float, int]
        try:
            self.dev.start(slave_address,0)
            self.dev.write(tx_data)
            self.dev.stop()
            time.sleep(read_delay)
            self.dev.start(slave_address,1)
            rxdata=self.dev.read(rx_length)
            self.dev.stop()
            return (self.STATUS_OK, None, rxdata),
        except Exception as e:
            return (self.STATUS_UNSPECIFIED_ERROR, e, ""),
    
    def open(self):
        self.dev =  i2cdriver.I2CDriver(self.port)
    
    def close(self):
        del self.dev
        
########################################################################################################################
class sen5xDevice(i2cDevice):
    """ Class providing support for Sensirion Sen5x air quality sensor (i2c).
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        if self.bridge: assert self.params['tty']
        else: assert self.params['bus']
        assert I2cConnection
        assert Sen5xI2cDevice
        if not 'driver' in self.params.keys(): self.params['driver']='sen5x'
        #if 'name' in self.params: self.name = self.params['name']+' %s' % (hex(self.params['address']))
        self.params['n_channels']=9
        self.config['channel_names']=['PM1.0',\
                                      'PM2.5',\
                                      'PM4.0',\
                                      'PM10.0',\
                                      'Humidity','Temperature','VOC_Index','NOx_Index','status']

        self.params['raw_units']=['µg/m^3','µg/m^3','µg/m^3','µg/m^3','%RH','degC','','','']
        self.config['eng_units']=['µg/m^3','µg/m^3','µg/m^3','µg/m^3','%RH','degC','','','']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        cprint( "Activating %s on i2c bus at %s with %i channels" % (self.params['driver'],hex(self.params['address']),self.params['n_channels']), 'green')

        # Default operating mode
        if not 'mode' in self.params: self.params['mode'] = 3 # ULTRAHIRES mode

        if self.bridge:
            self.i2c_transceiver = i2cdriver_interface(self.params['tty'])
        else:
            from sensirion_i2c_driver import LinuxI2cTransceiver
            self.i2c_transceiver = LinuxI2cTransceiver(self.params['bus'])
        self.device = Sen5xI2cDevice(I2cConnection(self.i2c_transceiver),self.params['address'])
        self.driverConnected=True
        
        # Get some device information
        self.config['ProductName']=self.device.get_product_name()[0]
        self.config['SerialNo']=self.device.get_serial_number()[0]
        self.config['Version']=self.device.get_version()[0]
        if not self.quiet:
            print("\tSen5x Version: {}".format(self.config['Version']))
            print("\tSen5x Product Name: {}".format(self.config['ProductName']))
            print("\tSen5x Serial Number: {}".format(self.config['SerialNo']))

        # Perform a device reset (reboot firmware)
        self.device.device_reset()
        
        # Start measurement mode on the device
        self.device.start_measurement()
        
        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):

        # Wait til ready
        if (self.device.read_data_ready()[0] is False) and (not self.quiet):
            print("\tSen5x: Waiting for data")
        while self.device.read_data_ready()[0] is False:
            time.sleep(0.01)

        # Read measured values -> clears the "data ready" flag
        values = self.device.read_measured_values()[0]
        mc_1p0 = values.mass_concentration_1p0.physical
        mc_2p5 = values.mass_concentration_2p5.physical
        mc_4p0 = values.mass_concentration_4p0.physical
        mc_10p0 = values.mass_concentration_10p0.physical
        ambient_rh = values.ambient_humidity.percent_rh
        ambient_t = values.ambient_temperature.degrees_celsius
        voc_index = values.voc_index.scaled
        nox_index = values.nox_index.scaled        

        # Read device status
        status = self.device.read_device_status()[0]
        
        self.lastValue = [mc_1p0, mc_2p5, mc_4p0, mc_10p0, ambient_rh, ambient_t, voc_index, nox_index, status.value]
        
        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        self.device.stop_measurement()
        time.sleep(.01)
        del self.device
        del self.i2c_transceiver

