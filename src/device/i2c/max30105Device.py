"""
    MAX30105 optical sensor

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.2.2
    @date 10/02/2022
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
    from max30105 import MAX30105, HeartRate
except ImportError:
    cprint("Please install max30105 library using pip")

########################################################################################################################
class max30105Device(i2cDevice):

    """ Class providing support for __
        Specify I2C bus and address on initialisation.
    """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        if 'name' in self.params: self.name = self.params['name']+' %i:%s' % (self.params['bus'],hex(self.params['address']))
        if not 'driver' in self.params.keys(): self.params['driver']=None

        self.params['n_channels']=4
        if not 'channel_names' in self.config:
            self.config['channel_names']=['Temperature','Instantaneous reading','Running mean','Delta']

        self.params['raw_units']=['degC','','','']
        self.config['eng_units']=['degC','','','']
        self.config['scale']=np.ones(self.params['n_channels'],)
        self.config['offset']=np.zeros(self.params['n_channels'],)
        if ('untitled' in self.name.lower()) or (self.name==''):
            self.name = 'MAX30105 optical sensor I2C %i:%s' % (self.params['bus'],self.params['address'])

        self.max30105 = MAX30105()
        self.max30105.setup(leds_enable=3)

        self.max30105.set_led_pulse_amplitude(1, 0.0)
        self.max30105.set_led_pulse_amplitude(2, 0.0)
        self.max30105.set_led_pulse_amplitude(3, 12.5)

        self.max30105.set_slot_mode(1, 'red')
        self.max30105.set_slot_mode(2, 'ir')
        self.max30105.set_slot_mode(3, 'green')
        self.max30105.set_slot_mode(4, 'off')

        self.hr = HeartRate(self.max30105)

        return

    # Apply configuration
    def apply_config(self):
        # Currently no configurable parameters.
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):

        data=[]
        means=[]
        mean_size=20; delta_size=10
        delta=0; deltas=[]
        while len(means)<mean_size+1:
            samples = self.max30105.get_samples()
            if samples is not None:
                if len(samples)>2:
                    r = samples[2] & 0xff
                    d = self.hr.low_pass_fir(r)
                    data.append(d)
                    if len(data) > mean_size:
                        data.pop(0)
                    mean = sum(data) / float(len(data))
                    means.append(mean)
                    if len(means) > delta_size:
                        delta = means[-1] - means[-delta_size]
                    else:
                        delta = 0
                    deltas.append(delta)
            time.sleep(0.01)


        self.lastValue = [self.max30105.get_temperature(),d,mean,np.mean(deltas)]

        self.updateTimestamp()

        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
            
        return

    # End connection to device.
    def deactivate(self):
        self.max30105.soft_reset()
        del self.max30105
        del self.hr
