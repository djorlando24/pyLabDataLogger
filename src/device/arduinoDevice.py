"""
    Serial device class - arduino like devices that talk over a USB to serial TTY
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 12/10/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

from serialDevice import serialDevice
import numpy as np
import datetime, time

try:
    import serial
except ImportError:
    print "Please install pySerial"
    raise

########################################################################################################################
class arduinoSerialDevice(serialDevice):
    """ Class defining an Arduino type microcontroller that communicates over the serial
        port, typically via USB. """

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self, reset=False, buffer_limit=1024):
    
        # Check
        try:
            assert(self.Serial)
            if self.Serial is None: raise IOError
        except:
            print "Serial connection to Arduino device is not open."
        
        # The serial arduino device should report repeated strings with the structure
        # DESCRIPTION: VARIABLE = VALUE UNITS, VARIABLE = VALUE UNITS\n
        
        nbytes=0
        desc=''
        while nbytes<buffer_limit:
            desc += self.Serial.read(1)
            if desc[-1] == ':':
                desc=desc[:-1]
                break
            nbytes+=1

        # First pass?
        values=[]
        if not 'channel_names' in self.params.keys() or reset:
            reset=True
            self.params['channel_names']=[]
            self.params['raw_units']=[]
            self.config['eng_units']=[]
            self.params['n_channels']=0
            self.name = desc
            print '\t',self.name
    
            while self.config['eng_units'] == []:
                nbytes=0; s=''
                while nbytes<buffer_limit:
                    s+=self.Serial.read(1)
                    if s[-1] == '=':
                        self.params['channel_names'].append(s[:-2].strip())
                        self.params['n_channels']+=1
                        break
                    nbytes+=1
                
                nbytes=0; s=''
                while nbytes<buffer_limit:
                    s+=self.Serial.read(1)
                    if s[-1] == ' ' and len(s)>1:
                        values.append( float(s.strip()) )
                        break
                    nbytes+=1
                
                nbytes=0; s=''
                while nbytes<buffer_limit:
                    s+=self.Serial.read(1)
                    if s[-1] == ',' or s[-1] == '\n':
                        self.params['raw_units'].append( s[:-1].strip() )
                        break
                    nbytes+=1
                
                if s[-1] == '\n':
                    self.config['eng_units']=self.params['raw_units']
                    break
                elif s[-1] != ',':
                    while self.Serial.read(1) != ',': pass

            if not 'scale' in self.config.keys():
                self.config['scale'] = np.ones(self.params['n_channels'],)
            if not 'offset' in self.config.keys():
                self.config['offset'] = np.zeros(self.params['n_channels'],)


        else:
            # Repeat query, no need to worry about the description and variable names
            nbytes=0; s=''; invar=False
            while nbytes<buffer_limit:
                s+=self.Serial.read(1)
                if s[-1] == '=':
                    s=''; nbytes=0
                    invar=True
                    s+=self.Serial.read(1)
                if s[-1] == ' ' and invar and len(s) > 1:
                    values.append( float(s.strip()) )
                    s=''; nbytes=0
                    invar=False
                    s+=self.Serial.read(1)
                if s[-1] == '\n': break
                nbytes+=1
    
        self.lastValue = np.array(values)
        self.lastScaled = np.array(self.lastValue) * self.config['scale'] + self.config['offset']
        self.updateTimestamp()
        
        return self.lastValue
