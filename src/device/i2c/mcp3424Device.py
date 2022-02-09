"""
    MCP3424 I2C Analog to Digital Converter Class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2
    @date 09/02/2022
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


########################################################################################################################
class mcp3424Device(i2cDevice):
    """ Class providing support for MCP3424 analog to digital converter.
        Channel gains can be specified with the gain config parameter (a list).
        Setting 'differential' parameter True gives 2 outputs instead of 4. """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        if not 'driver' in self.params.keys(): self.params['driver']='mcp3424'

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

        cprint( "Activating %s on i2c bus at %i:%s with %i channels" % (self.params['driver'],self.params['bus'],hex(self.params['address']),self.params['n_channels']) , 'green' )
        
        self.ADC = _mcp3424();
        self.config['RAW_MIN']=0
        self.config['V_MIN']=0
        self.fd='/dev/i2c-%i' % self.params['bus']
        if self.config['bits']==12:
            _mcp3424_init(self.ADC, self.fd, int(self.params['address'],16), MCP3424_RESOLUTION_12);
            self.config['RAW_MAX']=2048
        elif self.config['bits']==14:
            _mcp3424_init(self.ADC, self.fd, int(self.params['address'],16), MCP3424_RESOLUTION_14);
            self.config['RAW_MAX']=8192
        elif self.config['bits']==16:
            _mcp3424_init(self.ADC, self.fd, int(self.params['address'],16), MCP3424_RESOLUTION_16);
            self.config['RAW_MAX']=32768
        elif self.config['bits']==18:
            _mcp3424_init(self.ADC, self.fd, int(self.params['address'],16), MCP3424_RESOLUTION_18);
            self.config['RAW_MAX']=131072
        else:
            raise ValueError("Unknown MCP3424 bit depth (must be 12/14/16/18)")

        if self.diffDefault: print("\tDifferential mode (default)")
        elif self.diff: print("\tDifferential mode specified")
        else: print("\tSingle-ended mode")
        
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = '%s I2C %i:%s' % (self.params['driver'],self.params['bus'],self.params['address'])

        self.apply_config()
        self.driverConnected=True
        
        return

    # Apply configuration
    def apply_config(self):
        if self.params['pga']==1:
            _mcp3424_set_pga(self.ADC, MCP3424_PGA_1X);
            self.config['V_MAX']=5.06
        elif self.params['pga']==2:
            _mcp3424_set_pga(self.ADC, MCP3424_PGA_2X);
            self.config['V_MAX']=5.06/2.
        elif self.params['pga']==4:
            _mcp3424_set_pga(self.ADC, MCP3424_PGA_4X);
            self.config['V_MAX']=5.06/4.
        elif self.params['pga']==8:
            _mcp3424_set_pga(self.ADC, MCP3424_PGA_8X);
            self.config['V_MAX']=5.06/8.
        else:
            raise ValueError("Invalid MCP3424 PGA gain (must be 1/2/4/8)")
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        # Read all the ADC channel values in a list.
        values = [0]*4
        res = [0]*4
        c = [MCP3424_CHANNEL_1, MCP3424_CHANNEL_2, MCP3424_CHANNEL_3, MCP3424_CHANNEL_4]
        for i in range(4):
            res[i] = _mcp3424_get_raw(self.ADC, c[i]);
            values[i] = _MAP(res[i], self.config['RAW_MIN'], self.config['RAW_MAX'], self.config['V_MIN'], self.config['V_MAX']); 
        self.updateTimestamp()
        
        if self.diff:
            self.lastValue=[values[0]-values[1],values[2]-values[3]]
        else:
            self.lastValue=values

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        del self.ADC

