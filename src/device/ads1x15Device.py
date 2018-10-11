"""
    Adafruit ADS1x15 Analog to Digital Converter Class
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 1.0.0
    @date 07/06/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from i2cDevice import *
import datetime, time
import numpy as np

try:
    import Adafruit_ADS1x15
except ImportError:
    print "Error, could not load Adafruit_ADS1x15 library"

########################################################################################################################
class ads1x15Device(i2cDevice):
    """ Class providing support for Adafruit's ADS1x15 breakout boards (ADS1015, ADS1115).
        Specify I2C bus, address and driver (ADS1015/ADS1115) on initialisation.
        Channel gains can be specified with the gain config parameter (a list).
        Setting 'differential' parameter True gives 2 outputs instead of 4. """

    # Establish connection to device
    def activate(self):
        assert self.params['address']
        assert self.params['bus']
        if not 'driver' in self.params.keys(): self.params['driver']='ADS1115'

        if self.params['driver']=='ADS1115':
            self.ADC =  Adafruit_ADS1x15.ADS1115(address=self.params['address'], busnum=self.params['bus'])
        elif self.params['driver']=='ADS1015':
            self.ADC =  Adafruit_ADS1x15.ADS1015(address=self.params['address'], busnum=self.params['bus'])
        else:
            print "Error: unknown driver. Choices are ADS1015 or ADS1115"
            return

        if not 'differential' in self.params.keys(): self.diff=True

        if self.diff:
            self.config['n_channels']=2
            self.config['channel_names']=['ChA','ChB']
        else:
            self.config['n_channels']=4
            self.config['channel_names']=['Ch1','Ch2','Ch3','Ch4']

        self.params['raw_units']=['V']*self.config['n_channels']
        self.config['eng_units']=['V']*self.config['n_channels']
        self.config['scale']=np.ones(self.config['n_channels'],)
        self.config['offset']=np.zeros(self.config['n_channels'],)

        self.apply_config()
        self.driverConnected=True
        print self.query()
        return

    # Apply configuration (i.e. gain parameter)
    def apply_config(self):
        assert self.diff
        valid_gain_values=[2/3, 1,2,4,8,16]
        if not 'gain' in self.config.keys(): self.config['gain']=[2/3]*self.config['n_channels']
        for chg in self.config['gain']:
            if not chg in valid_gain_values:
                print "Error, gain values are invalid. Resetting"
                self.config['gain']=[2/3]*self.config['n_channels']
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        try:
            assert self.ADC
            # Read all the ADC channel values in a list.
            values = [0]*4
            for i in range(4):
                values[i] = adc.read_adc(i, gain=GAIN)*4.096/32768.
            self.updateTimestamp()
            
            if self.diff:
                self.lastValue=[values[0]-values[1],values[2]-values[3]]
            else:
                self.lastValue=values

            self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
        except:
            raise
            
        return

    # End connection to device.
    def deactivate(self):
        del self.ADC

if __name__ == '__main__':
    D=ads1x15Device({'address':0x49})
    while True:
        time.sleep(1)
        print D.query()


