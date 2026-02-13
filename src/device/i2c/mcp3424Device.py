#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    MCP3424 I2C Analog to Digital Converter Class
    
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
import site, itertools, glob, datetime, os, time
import numpy as np
from termcolor import cprint

# Ctypes required
import ctypes, ctypes.util, struct
from ctypes import py_object, c_int, c_char, c_uint, c_char_p, c_uint8, cast, POINTER, addressof

# set up enums and structs
(MCP3424_CHANNEL_1,MCP3424_CHANNEL_2,MCP3424_CHANNEL_3,MCP3424_CHANNEL_4)=range(4)
(MCP3424_CONVERSION_MODE_ONE_SHOT,MCP3424_CONVERSION_MODE_CONTINUOUS)=range(2)
(MCP3424_PGA_1X,MCP3424_PGA_2X,MCP3424_PGA_4X,MCP3424_PGA_8X)=range(4)
(MCP3424_RESOLUTION_12,MCP3424_RESOLUTION_14,MCP3424_RESOLUTION_16,MCP3424_RESOLUTION_18)=range(4)
mcp3424_resolution_t=c_char
mcp3424_pga_t=c_char
mcp3424_channel_t=c_char
mcp3424_conversion_mode_t=c_char

class mcp3424_t(ctypes.Structure):
     _fields_ = [("df", c_int),
                 ("addr", c_uint8),
                 ("config", c_uint8),
                 ("err", c_int),
                 ("errstr", c_char*256),
                 ]

########################################################################################################################
class mcp3424Device(i2cDevice):
    """ Class providing support for MCP3424 analog to digital converter.
        Channel gains can be specified with the gain config parameter (a list).
        Setting 'differential' parameter True gives 2 outputs instead of 4. """

    # Establish connection to device
    def activate(self):
        # Load dynamic library

        # Find DLLs for specific devices generated at build time
        sites = site.getsitepackages(); sites.append(site.USER_SITE)
        libname = 'mcp3424'
        for libext in ['so','dylib','dll','a']:
            path_to_lib = list(itertools.chain.from_iterable([ glob.glob(p+'/lib'+libname+'*.'+libext)\
                                        for p in sites ]))
            if len(path_to_lib)>0: break
        if len(path_to_lib)==0: cprint("\tWarning - can't find lib%s" % libname,'yellow')
        else: self.libpath = path_to_lib[0]
        self.L = ctypes.cdll.LoadLibrary(self.libpath)
        
        # Set up the functions we'll call later
        self.L.mcp3424_init.argtypes=[POINTER(mcp3424_t), c_char_p, c_uint8, mcp3424_resolution_t]
        self.L.mcp3424_init.restype=None
        self.L.mcp3424_set_pga.argtypes=[POINTER(mcp3424_t), mcp3424_pga_t]
        self.L.mcp3424_set_pga.restype=None
        self.L.mcp3424_get_raw.argtypes=[POINTER(mcp3424_t), mcp3424_channel_t]
        self.L.mcp3424_get_raw.restype=c_uint
        self.L.mcp3424_close.argtypes=[POINTER(mcp3424_t)]
        self.L.mcp3424_set_conversion_mode.argtypes=[POINTER(mcp3424_t), mcp3424_conversion_mode_t]
        self.L.mcp3424_set_conversion_mode.restype=None
        #self.L.mcp3424_set_resolution.argtypes=[mcp3424_t, mcp3424_resolution_t]
        #self.L.mcp3424_set_resolution.restype=None

        # Set up device
        assert self.params['address']
        assert self.params['bus']
        if not 'driver' in self.params.keys(): self.params['driver']='mcp3424'
        if 'name' in self.params: self.name = self.params['name']+' %i:%s' % (self.params['bus'],hex(self.params['address']))

        if not 'differential' in self.params.keys(): 
            self.diffDefault=False
            self.diff=False
        else: 
            self.diffDefault=False
            self.diff=self.params['differential']

        if self.diff:
            self.params['n_channels']=2
            if not 'channel_names' in self.config:
                self.config['channel_names']=['Ch1-2','Ch3-4']
        else:
            self.params['n_channels']=4
            if not 'channel_names' in self.config:
                self.config['channel_names']=['Ch1','Ch2','Ch3','Ch4']


        self.params['raw_units']=['V']*self.params['n_channels']
        self.config['eng_units']=['V']*self.params['n_channels']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        
        if not 'pga' in self.params: self.params['pga']=1
        if 'bits' in self.params: self.config['bits']=self.params['bits']
        else: self.config['bits']=18

        cprint( "Activating %s on i2c bus at %i:%s with %i channels" % (self.params['driver'],\
                self.params['bus'],hex(self.params['address']),self.params['n_channels']) , 'green' )
        
        self.ADC = mcp3424_t()
        self.config['RAW_MIN']=0
        self.i2c_dev='/dev/i2c-%i' % self.params['bus']
        '''
        self.L.mcp3424_init.argtypes=[mcp3424_t, c_int, c_uint8, mcp3424_resolution_t]
        self.L.mcp3424_init.restype=None
        self.L.mcp3424_set_pga.argtypes=[mcp3424_t, mcp3424_pga_t]
        self.L.mcp3424_set_pga.restype=None
        self.L.mcp3424_get_raw.argtypes=[mcp3424_t, mcp3424_channel_t]
        self.L.mcp3424_get_raw.restype=c_uint
        '''
        if self.config['bits']==12:
            self.L.mcp3424_init(self.ADC, c_char_p(self.i2c_dev.encode('ascii')), c_uint8(self.params['address']), MCP3424_RESOLUTION_12);
            self.config['RAW_MAX']=2048
        elif self.config['bits']==14:
            self.L.mcp3424_init(self.ADC, c_char_p(self.i2c_dev.encode('ascii')), c_uint8(self.params['address']), MCP3424_RESOLUTION_14);
            self.config['RAW_MAX']=8192
        elif self.config['bits']==16:
            self.L.mcp3424_init(self.ADC, c_char_p(self.i2c_dev.encode('ascii')), c_uint8(self.params['address']), MCP3424_RESOLUTION_16);
            self.config['RAW_MAX']=32768
        elif self.config['bits']==18:
            self.L.mcp3424_init(self.ADC, c_char_p(self.i2c_dev.encode('ascii')), c_uint8(self.params['address']), MCP3424_RESOLUTION_18);
            self.config['RAW_MAX']=131072
        else:
            raise ValueError("Unknown MCP3424 bit depth (must be 12/14/16/18)")

        self.L.mcp3424_set_conversion_mode(self.ADC, MCP3424_CONVERSION_MODE_ONE_SHOT);

        if self.diffDefault: print("\tDifferential mode (default)")
        elif self.diff: print("\tDifferential mode specified")
        else: print("\tSingle-ended mode")
        
        self.apply_config()
        self.driverConnected=True
        
        return

    # Apply configuration
    def apply_config(self):
        if self.params['pga']==1:
            self.L.mcp3424_set_pga(self.ADC, MCP3424_PGA_1X);
            self.config['V_MAX']=2.048
        elif self.params['pga']==2:
            self.L.mcp3424_set_pga(self.ADC, MCP3424_PGA_2X);
            self.config['V_MAX']=2.048/2.
        elif self.params['pga']==4:
            self.L.mcp3424_set_pga(self.ADC, MCP3424_PGA_4X);
            self.config['V_MAX']=2.048/4.
        elif self.params['pga']==8:
            self.L.mcp3424_set_pga(self.ADC, MCP3424_PGA_8X);
            self.config['V_MAX']=2.048/8.
        else:
            raise ValueError("Invalid MCP3424 PGA gain (must be 1/2/4/8)")
        self.config['V_MIN']=-self.config['V_MAX']
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        # Read all the ADC channel values in a list.
        values = [0]*4
        res = [0]*4
        c = [MCP3424_CHANNEL_1, MCP3424_CHANNEL_2, MCP3424_CHANNEL_3, MCP3424_CHANNEL_4]
        for i in range(4):
            res[i] = self.L.mcp3424_get_raw(self.ADC, c_char(c[i]));
            values[i] = ((res[i] - self.config['RAW_MIN']) * \
                    ((self.config['V_MAX'] - self.config['V_MIN']) / (self.config['RAW_MAX'] - self.config['RAW_MIN']))) \
                    + self.config['V_MIN'] 
        self.updateTimestamp()
        
        if self.diff:
            self.lastValue=[values[0]-values[1],values[2]-values[3]]
        else:
            self.lastValue=values

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        self.L.mcp3424_close(self.ADC)
        del self.ADC

