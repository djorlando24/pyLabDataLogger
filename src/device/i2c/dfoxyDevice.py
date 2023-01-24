#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    DFRobot Oxygen Sensor class

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2023 LTRAC
    @license GPL-3.0+
    @version 1.3.0
    @date 23/12/2022
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
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
    import smbus
except ImportError:
    cprint( "Error, smbus module could not be loaded", 'red', attrs=['bold'])

########################################################################################################################
class dfoxyDevice(i2cDevice):

    """ Class providing support for DFRobot Oxygen Sensor.
    https://wiki.dfrobot.com/Gravity_I2C_Oxygen_Sensor_SKU_SEN0322#target_6
        Specify I2C bus and address on initialisation.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        if not 'driver' in self.params.keys():  self.params['driver']='dfoxy'
        if 'name' in self.params: self.name = self.params['name']+' %i:%s' % (self.params['bus'],hex(self.params['address']))
        self.params['n_channels']=1
        if not 'channel_names' in self.config:
            self.config['channel_names']=['O2_Vol']

        self.params['raw_units']=['%']
        self.config['eng_units']=['%']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)

        self.COLLECT_NUMBER   = 10              # collect number, the collection range is 1-100
        #self.IIC_MODE         = 0x01            # default use IIC1
        self.IIC_MODE=self.params['bus']

        cprint( "Activating %s on i2c bus at %i:%s with %i channels" % (self.params['driver'],self.params['bus'],hex(self.params['address']),self.params['n_channels']) , 'green' )

        self.oxygen = DFRobot_Oxygen_IIC(self.IIC_MODE , self.params['address'])

        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):

        self.lastValue = [ self.oxygen.get_oxygen_data(self.COLLECT_NUMBER) ]

        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        pass

'''!
  The following class has been adapted from the following:

  @brief 定义DFRobot_Oxygen 类的基础结构，基础方法的实现
  @copyright Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @license The MIT License (MIT)
  @author [ZhixinLiu](zhixin.liu@dfrobot.com)
  @version V1.0
  @date 2021-10-22
  @url https://github.com/DFRobot/DFRobot_Oxygen
'''


OXYGEN_DATA_REGISTER      = 0x03
USER_SET_REGISTER         = 0x08
AUTUAL_SET_REGISTER       = 0x09
GET_KEY_REGISTER          = 0x0A

class DFRobot_Oxygen(object):
  __key      = 0.0
  __count    = 0
  __txbuf      = [0]
  __oxygendata = [0]*101
  def __init__(self, bus):
    self.i2cbus = smbus.SMBus(bus)

  def get_flash(self):
    rslt = self.read_reg(GET_KEY_REGISTER, 1)
    if rslt == 0:
      self.__key = (20.9 / 120.0)
    else:
      self.__key = (float(rslt[0]) / 1000.0)
    time.sleep(0.1)
 
  def calibrate(self, vol, mv):
    self.__txbuf[0] = int(vol * 10)
    if (mv < 0.000001) and (mv > (-0.000001)):
      self.write_reg(USER_SET_REGISTER, self.__txbuf)
    else:
      self.__txbuf[0] = int((vol / mv) * 1000)
      self.write_reg(AUTUAL_SET_REGISTER, self.__txbuf)

  def get_oxygen_data(self, collect_num):
    self.get_flash()
    if collect_num > 0:
      for num in range(collect_num, 1, -1):
        self.__oxygendata[num-1] = self.__oxygendata[num-2]
      rslt = self.read_reg(OXYGEN_DATA_REGISTER, 3)
      self.__oxygendata[0] = self.__key * (float(rslt[0]) + float(rslt[1]) / 10.0 + float(rslt[2]) / 100.0)
      if self.__count < collect_num:
        self.__count += 1
      return self.get_average_num(self.__oxygendata, self.__count)
    elif (collect_num > 100) or (collect_num <= 0):
      return -1

  def get_average_num(self, barry, Len):
    temp = 0.0
    for num in range (0, Len):
      temp += barry[num]
    return (temp / float(Len))

class DFRobot_Oxygen_IIC(DFRobot_Oxygen): 
  def __init__(self, bus, addr):
    self.__addr = addr
    super(DFRobot_Oxygen_IIC, self).__init__(bus)

  def write_reg(self, reg, data):
    self.i2cbus.write_i2c_block_data(self.__addr, reg, data)

  def read_reg(self, reg, len):
    while 1:
      try:
        rslt = self.i2cbus.read_i2c_block_data(self.__addr, reg, len)
        return rslt
      except:
        raise pyLabDataLoggerIOError("DFRobot oxygen sensor read_reg")
