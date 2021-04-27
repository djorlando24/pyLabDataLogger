"""
    Main device class for pyPiDataLogger
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.3
    @date 22/03/2021
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

    Changes:
        22/02/2019 - Added logging options
        30/07/2020 - handle mixed array and float types
"""

import datetime
import numpy as np
import sys, os
from termcolor import cprint

try:
    import h5py
except ImportError:
    cprint( "Install h5py library to enable HDF5 logging support.", 'red', attrs=['bold'])

class pyLabDataLoggerIOError(IOError):
    """ Exception raised when an IO error occurs in a driver.
        Generally IO errors can be handled with generic IOError
        but this exception is particularly for timeouts on blocking
        communication routines, which are caught and should only give
        a brief warning, and failures to connect to a previously setup
        device (ie something got unplugged while the code was running)
    """
    def __init__(self, *args, **kwargs):
        # Call the base class constructor with the parameters it needs
        super(pyLabDataLoggerIOError, self).__init__(*args,**kwargs)
        cprint( "\tIO Error:", 'red', attrs=['bold'])
        cprint( "\t"+''.join(args), 'red')
        pass



class device:
    """ Main class defining a device in pyPiDataLogger.
        This class is inherited by more specific sub-categories of devices i.e. USB. """

    def __init__(self, quiet=True, **kwargs):
        self.config = {} # user-variable configuration parameters go here (ie scale, offset, eng. units)
        self.params = {} # fixed configuration paramaters go here (ie USB PID & VID, raw device units)
        self.driverConnected = False # Goes to True when scan method succeeds
        self.name = "untitled device"
        self.lastValue = None # Last known value (for logging)
        self.lastValueTimestamp = None # Time when last value was obtained
        
        if 'quiet' in kwargs: self.quiet = kwargs['quiet']
        else: self.quiet=quiet
        
        pass

    # Detect if device is present
    def scan(self):
        cprint( "scan method not yet implemented for",self.name, 'red', attrs=['bold'])

    # Establish connection to device (ie open serial port)
    def activate(self):
        # self.driverConnected=True
        cprint( "activate method not yet implemented for",self.name, 'red', attrs=['bold'])

    # Deactivate connection to device (ie close serial port)
    def deactivate(self):
        self.driverConnected=False
        cprint( "deactivate method not yet implemented for",self.name, 'red', attrs=['bold'])

    # Apply configuration changes to the driver
    def apply_config(self):
        cprint( "apply_config not yet implemented for",self.name, 'red', attrs=['bold'])

    # Update configuration (ie change sample rate or number of samplezzs)
    def update_config(self,config_keys={}):
        for key in config_keys.keys():
            self.config[key]=self.config_keys[key]
        self.apply_config()
        return

    # Update device with new value, update lastValue and lastValueTimestamp
    def query(self):
        return self.lastValue

    def updateTimestamp(self):
        self.lastValueTimestamp = datetime.datetime.now()

    # Re-establish connection to device.
    def reset(self):
        self.deactivate()
        self.scan()
        if self.driverConnected: self.activate()
        else: cprint( "Error resetting %s: device is not detected" % self.name, 'red', attrs=['bold'])

    # Check if the device is a video type (ie for animating loops, handling output)
    def isVideo(self):
        if ('opencv' in self.driver) or ('v4l2' in self.driver): return True
        else: return False
    

    ###########################################################################################################################################
    # Print values with units in a nice readable format.
    def pprint(self,lead='\t',maxarrayvalues=12):
        show_scaled = ('eng_units' in self.config) and ('scale' in self.config) and\
                      ('offset' in self.config) and ('eng_units' in self.config) and\
                      not (np.all(np.array(self.config['scale'])==1.) and  np.all(np.array(self.config['offset'])==0.))
                                            
        # Print scalar variables with units where present. ################################################
        if (not isinstance( self.lastValue[0], list)) and (not isinstance(self.lastValue[0], np.ndarray)):
            if 'raw_units' in self.params:
                sys.stdout.write(lead+'Raw values: ')
                for n in range(self.params['n_channels']):

                    if isinstance(self.lastValue[n],str):
                        if self.params['raw_units'][n] == '':
                            sys.stdout.write(u'%s = %s' % (self.config['channel_names'][n],self.lastValue[n]))
                        else:
                            sys.stdout.write(u'%s = %s %s' % (self.config['channel_names'][n],\
                                                                self.lastValue[n],\
                                                                self.params['raw_units'][n]))
                    
                    else: # If numeric, use %g which will format big/smaller numbers in exp. notation.
                        if self.params['raw_units'][n] == '':
                            sys.stdout.write(u'%s = %g' % (self.config['channel_names'][n],self.lastValue[n]))
                        else:
                            sys.stdout.write(u'%s = %g %s' % (self.config['channel_names'][n],\
                                                                self.lastValue[n],\
                                                                self.params['raw_units'][n]))

                    # Spacing between variables.
                    # New line every 4 vars, commas between them 
                    if (((n%4)==3) & (n>0)): sys.stdout.write('\n'+lead)                      
                    elif (n<self.params['n_channels']-1): sys.stdout.write(', ')

                sys.stdout.write('\n')
                
            else: # I have no idea what is in self.lastValue, print verbatim!
                print(lead+'Raw values:',self.lastValue)
            
            # Only show the scaled units if they exist.
            if show_scaled:
                for n in range(self.params['n_channels']):
                    sys.stdout.write(u'%f %s, ' % (self.lastScaled[n],self.config['eng_units'][n])) 
                sys.stdout.write('\n')
    
        # Vectors (i.e. timeseries data) with units added to the end where present. ####################################
        else:
            for n in range(self.params['n_channels']):
                if not isinstance(self.lastValue[n], np.ndarray):
                    if self.params['raw_units'][n] == '':
                        sys.stdout.write(u'%s = %s' % (self.config['channel_names'][n],self.lastValue[n]))
                    else:
                        sys.stdout.write(u'%s = %s %s' % (self.config['channel_names'][n],\
                                                          self.lastValue[n],\
                                                          self.params['raw_units'][n]))
                    sys.stdout.write('\n')
                else: 
                    # show some values of 1-D lists and arrays
                    if (len(self.lastValue[n].shape) <= 1):
                    
                        # Limit how many values to print
                        ismore=''
                        if ( isinstance( self.lastValue[n], list) or isinstance(self.lastValue[n], np.ndarray) ):
                            if len(self.lastValue[n])>maxarrayvalues:
                                nn=maxarrayvalues
                                lv=self.lastValue[n][:nn]
                                lvs=self.lastScaled[n][:nn]
                                ismore='...& %i more values' % (len(self.lastValue[n]) - maxarrayvalues)
                            else:
                                nn=len(self.lastValue[n])
                                lv=self.lastValue[n]
                                lvs=self.lastScaled[n]

                        else:
                            lv=self.lastValue[n]
                            lvs=self.lastScaled[n]
                            
                        if ~show_scaled: print(lead+u'%i: %s = %s %s %s' % (n,self.config['channel_names'][n],\
                                                           lv,self.params['raw_units'][n],ismore))
                        else: print(lead+u'%i: %s = %s%s %s \t %s %s %s' % (n,self.config['channel_names'][n],lv,\
                                                              self.params['raw_units'][n],ismore,\
                                                            lvs,self.config['eng_units'][n],ismore))
                    
                    # Don't show N-D arrays where N>1
                    else:
                        if ~show_scaled: print(lead+u'%i: %s = <array of size %s> %s' % (n,self.config['channel_names'][n],\
                                            self.lastValue[n].shape,self.params['raw_units'][n]))
                        else: print(lead+u'%i: %s = <array of size %s> %s \t <array of size %s> %s' % (n,\
                                self.config['channel_names'][n],self.lastValue[n].shape,\
                                self.params['raw_units'][n],\
                                self.lastScaled[n].shape,self.config['eng_units'][n]))
                    
        return

    ################################################################################################################################################################
    # log data to files
    def log(self, filename):
        e = os.path.splitext(filename)[-1]
        if ('hdf5' in e) or ('h5' in e): self.log_hdf5(filename)
        elif ('txt' in e) or ('csv' in e) or ('log' in e): self.log_text(filename)
        else: raise ValueError("Unknown/unsupported logging format %s" % e)

    # log to HDF5 file
    # max_records specifies the largest size an array can get.
    def log_hdf5(self, filename, max_records=4096):
        try:
            assert(h5py)
        except AssertionError:
            cprint( "Install h5py library to enable HDF5 logging support.", 'red', attrs=['bold'])
        
        # Open file
        with h5py.File(filename, 'a') as fh:

            # Load group for this device.
            if 'name' in self.config: devname = self.config['name']
            elif 'name' in self.params: devname = self.params['name']
            else: devname = self.name
            if devname in fh: dg = fh[devname]
            else: 
                dg = fh.create_group(devname)
                # On creation, add attributes from config and params
                for attr in self.params.keys(): 
                    dg.attrs[attr] = repr(self.params[attr])
                for attr in self.config.keys():
                    dg.attrs[attr] = repr(self.config[attr])

            # Create/update timestamp dataset
            # Each device has a lastValueTimestamp which can vary a bit between devices due to latency issues.
            if 'timestamp' in dg:
                td = dg['timestamp']
                td.resize([td.shape[0]+1,])
                td[-1] = self.lastValueTimestamp.strftime("%d-%b-%Y (%H:%M:%S.%f)").encode('ascii')
            else:
                dg.create_dataset('timestamp',data=[self.lastValueTimestamp.strftime("%d-%b-%Y (%H:%M:%S.%f)").encode('ascii')],maxshape=(max_records,))


            # Loop all channels of device
            for i in range(self.params['n_channels']):

                # Make/open group for channel
                if self.config['channel_names'][i] in dg: cg = dg[self.config['channel_names'][i]]
                else: cg = dg.create_group(self.config['channel_names'][i])

                # Loop over raw values and scaled values
                for data, desc, units in [(self.lastValue, "Raw values", self.params['raw_units'][i]),\
                                          (self.lastScaled, "Scaled values", self.config['eng_units'][i])]:

                    # h5py doesn't like unicode strings and nonetypes
                    if isinstance(data[i],str): data[i] = data[i].encode('ascii')
                    if data[i] is None: data[i]="None".encode('ascii')

                    if desc in cg:  # Add more
                        dset = cg[desc]
                        ds = list(dset.shape)
                        ds[-1] += 1
                        #if isinstance(data[i],list) or isinstance(data[i],np.ndarray):
                        #    if len(data[i]) > ds[0]: ds[0] = len(data[i])
                        dset.resize(ds)
                        dset[...,ds[-1]-1]=data[i]

                    else: # Make new array
                        ds = list(np.array(data[i]).shape) #;print("new hdf5 array size will be",ds)
                        ms=ds[:]
                        ds.append(1)
                        ms.append(max_records)
                        thedata=np.array(data[i]).reshape(tuple(ds))
                        dset = cg.create_dataset(desc, data=thedata, maxshape=ms)
                        dset.attrs['units']=units

                # Debugging output.
                #print '\n', self.name, self.config['channel_names'][i], 'logfile size:', dset.shape

            fh.close()

    # log to text file
    def log_text(self, filename):
        
        # Write header
        if not os.path.exists(filename):            
            fh = open(filename,'w')
            fh.write('# PyLabDataLogger text file\n')
            fh.write('# Started %s\n' % datetime.datetime.now())
            fh.write('#\n# DEVICE = %s\n' % self.name)
            fh.write('#\n# CONFIG:\n')
            for attr in self.config.keys():
                fh.write('#        %s = %s\n' % (attr,str(self.config[attr])))
            fh.write('#\n# PARAMS:\n')
            for attr in self.params.keys():
                fh.write('#        %s = %s\n' % (attr,str(self.params[attr])))
            fh.write('#\n# CHANNELS:\n')
            for i in range(self.params['n_channels']):
                fh.write('#        %s\n' % self.config['channel_names'][i])
            fh.write('\n')
            fh.close()

        # Write latest data
        fh = open(filename,'a')
        
        # Loop channels.
        for i in range(self.params['n_channels']):
            fh.write('# CHANNEL = %s, TIMESTAMP = %s, DEV = %s\n' % (self.config['channel_names'][i],self.lastValueTimestamp,self.name))
            # Loop over raw values and scaled values
            for data, desc, units in [(self.lastValue, "Raw values", self.params['raw_units'][i]),\
                                      (self.lastScaled, "Scaled values", self.config['eng_units'][i])]:
                fh.write('# %s, units = %s\n' % (desc,units))
                if isinstance(data[i],np.ndarray): np.savetxt(fh, data[i].T, delimiter=',')
                else: fh.write(str(data[i])+'\n')
                fh.write('\n')

        fh.close()
        
