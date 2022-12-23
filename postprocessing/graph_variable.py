#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    GRAPH VALUES OF PRERECORDED DATASETS
    
    Useful for applying new linear calibrations to previously collected data,
    for arbitrary voltage and current signals etc.
    
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

import sys, h5py, ast, os
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from termcolor import cprint

FAST_MODE=False
plottable_horiz_axis = []
plottable_vert_axis = []

try:
    from consolemenu import *
    from consolemenu.items import *
    from consolemenu.format import *
except ImportError:
    print("Please install console-menu module (pip3 install console-menu)")
    exit(1)

def adjust_calibration(*args):
    print(args)
    return

# Convert string timestamp to numeric time ##################################
def convert_timestamp(a):
    # strftime("%d-%b-%Y (%H:%M:%S.%f)").encode('ascii')
    # b'04-Feb-2022 (23:20:28.868890)'
    times=[]
    #for i in tqdm.tqdm(range(len(a))):
    for s in a[:]:
        d=datetime.strptime(s.decode('utf-8'),"%d-%b-%Y (%H:%M:%S.%f)")
        times.append(d)
    return times

# Use Matplotlib to make graphs #############################################
def do_plots(filenames):
    
    if len(plottable_vert_axis)<1: return
    if len(plottable_horiz_axis) != len(plottable_vert_axis):
        cprint("Mismatch in X and Y axes!",'red')
        return
    
    print("Plotting from files: "+str(filenames))
    print("Plotting variables: "+str(plottable_vert_axis))
    
    # Setup
    fig=plt.figure()
    ax=fig.add_subplot(111)
    axR=None
    plt.grid(alpha=.2)
    plt.xticks(rotation=45)
    
    ph=[]
    ll=[]
    n_vars=len(plottable_vert_axis)
    using_time=True
    first_loop=True
    
    if len(filenames)==1:
        plt.suptitle(filenames[0])
    
    # Read multiple files
    for file in filenames:
        all_x=[]
        all_y=[]
        all_u=[]
        
        # Read all data, and find earliest timestamp.
        try:
            H=h5py.File(file,'r')
            for i in range(len(plottable_horiz_axis)):
            
                if 'time' in plottable_horiz_axis[i]:
                    all_x.append(convert_timestamp(H[plottable_horiz_axis[i]]))
                    if first_loop: plt.xlabel("Timestamp")
                else:
                    all_x.append(H[plottable_horiz_axis[i]])
                    using_time=False
                    if first_loop: plt.xlabel(H[plottable_horiz_axis[i]])
            
                all_y.append(H[plottable_vert_axis[i]])
                all_u.append(H[plottable_vert_axis[i]].attrs['units'])
            
            # If 2 vars, use 2 vertical axes. Else all on 1 axis.
            # If 1-2 vars, use the y labels instead of a legend.
            if first_loop:
                if n_vars<2:
                    plt.ylabel('\n'.join(plottable_vert_axis[0].split('/'))+" ["+all_u[0]+"]")
                if n_vars==2:
                    plt.ylabel('\n'.join(plottable_vert_axis[0].split('/'))+" ["+all_u[0]+"] (Blue)") 
                    axR=ax.twinx()
                    plt.ylabel('\n'.join(plottable_vert_axis[1].split('/'))+" ["+all_u[1]+"] (Red)")
                first_loop=False
            
            # Convert time on horiz axis & make graph    
            for i in range(len(plottable_horiz_axis)):
                x=all_x[i]; y=all_y[i]
                if (n_vars==2) and (i==1): 
                    p0,=axR.plot(np.array(x),np.array(y),c='r',lw=1)
                else: 
                    p0,=ax.plot(np.array(x),np.array(y),lw=1)
                    ph.append(p0)
                    if len(filenames)==1:
                        ll.append(plottable_vert_axis[i]+' ['+all_u[i]+']')
                    else:
                        ll.append(os.path.basename(file)+'\n'+plottable_vert_axis[i]+' ['+all_u[i]+']')
            
            H.close()
    
        except KeyError:
            cprint("Problem with variable %s in file %s." % (plottable_vert_axis[i],file),'red')
            exit(1)
        except IOError:
            cprint("Can't read %s." % file,'red')
            exit(1)
        except:
            pass
    
    # Show the legend?
    if n_vars >2: 
        plt.legend(ph,ll,loc='lower left', mode='expand', bbox_to_anchor=(0, 1.02,1,0.2))
        plt.subplots_adjust(left=0.05,right=0.95,bottom=0.25,top=0.75)
    else:
        plt.subplots_adjust(left=0.15,right=0.85,bottom=0.25,top=0.95)    
    
    # format the X axis for time?
    if using_time: 
        total_sec = (plt.xlim()[1]-plt.xlim()[0])*86400
        if total_sec>604800:
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d-%b-%Y (%H:%M)"))            
        elif total_sec>86400:
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d-%b (%H:%M)"))
        elif total_sec>3600:
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        else:
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%M:%S.%f"))
            
    cprint("Drawing plot. Close window to exit program.",'yellow')
    plt.show()
    
    return
            


#### This code block will find all valid device groups in a HDF5 object ############

class deviceFinder:
    def __init__(self, h5py_obj=None):
        # Store an empty list for dataset names
        self.names = []
        
        if h5py_obj is not None:
            h5py_obj.visititems(self)
            
        return

    def __call__(self, name, h5obj):
        # Must be Group
        if isinstance(h5obj, h5py.Group):
            # Check Group's contents
            contents = []
            for ch in h5obj.values():
                if isinstance(ch, h5py.Group):
                    contents.extend(list(ch.keys()))
            # Must have attributes of a top-level device with scalable values;
            # (camera device types don't have the Raw values and Scaled values datasets)
            if ('channel_names' in h5obj.attrs.keys()) and ('Raw values' in contents):
                self.names += [name]
        return


#### This code block will find all valid plottable variables in a HDF5 object ############

class variableFinder:
    def __init__(self, h5py_obj=None):
        # Store an empty list for dataset names
        self.names = []
        self.units = []
        self.dtypes = []
        self.emptyVarCount=0
        self.stringVarCount=0
        
        if h5py_obj is not None:
            h5py_obj.visititems(self)
            
        return

    def __call__(self, name, h5obj):
        # Must be Group
        if isinstance(h5obj, h5py.Dataset):  # must be dataset
            #if ('units' in h5obj.attrs.keys()): # must have units attribute
            if ('S' in str(h5obj.dtype)) or ('O' in str(h5obj.dtype)) or ('obj' in str(h5obj.dtype)): # Must be numeric dtype
                self.stringVarCount+=1
                cprint(h5obj.name+'\t'+str(h5obj.dtype)+' (not plottable type)','red')
            else:
                if FAST_MODE: # no empty-array check
                    cprint(h5obj.name+'\t'+str(h5obj.dtype),'green',attrs=['bold'])
                    self.names += [name]
                    self.units += [h5obj.attrs['units']]
                    self.dtypes += [str(h5obj.dtype)]
                else:                
                    if (np.any(np.nan_to_num(h5obj[...])!=0)): # Not all NaN or zero
                        cprint(h5obj.name+'\t'+str(h5obj.dtype),'green',attrs=['bold'])
                        self.names += [name]
                        self.units += [h5obj.attrs['units']]
                        self.dtypes += [str(h5obj.dtype)]
                    else:
                        cprint(h5obj.name+'\t'+str(h5obj.dtype)+' (empty variable)','yellow')
                        self.emptyVarCount += 1

                            
        return
   
###############################################################################################

# Read attribute array from device and turn it into a real python list.
def read_attr_array(b):
    s = b.replace('array(','(').replace('nan','0')
    try:
        return ast.literal_eval(s)
    except ValueError as e:
        print(s)
        raise


# Function that graphs variables ##############################################################
def select_var(filenames, dev_name, var_name):
    plottable_vert_axis.append(dev_name+'/'+var_name)
    plottable_horiz_axis.append(dev_name+'/timestamp')
    return

# Make a menu that selects a device & channel #################################################
def main(filenames):

    # Open 1st file for dev/channel selection
    H=h5py.File(filenames[0],'r')
    
    # Make menu to select device
    menu_format = MenuFormatBuilder().set_border_style_type(MenuBorderStyleType.HEAVY_BORDER) \
    .set_prompt("SELECT>") \
    .set_title_align('center') \
    .set_subtitle_align('center') \
    .set_border_style_type(MenuBorderStyleType.DOUBLE_LINE_BORDER)\
    .set_left_margin(4) \
    .set_right_margin(4) \
    .show_header_bottom_border(True)
    
    dev_menu = ConsoleMenu("CHOOSE A DEVICE","File: %s" % filenames[0],\
                           formatter=menu_format)
    
    
    cprint("Scanning file...", 'cyan')
    
    # List devices, with channels in each
    for k in deviceFinder(H).names:
    
        #  Get all channel info          
        channels = variableFinder(H[k])
        channel_descriptors = []
        for i in range(len(channels.names)):
            channel_descriptors.append('%s [%s]' % (channels.names[i],channels.units[i]))
        
       
        # Make submenu for selecting channel
        channel_menu = ConsoleMenu("SELECT A CHANNEL/VARIABLE: Device = %s" % k,\
                   "%i empty vars not shown, %i non-numeric vars not shown" % (channels.emptyVarCount,channels.stringVarCount))
        for i in range(len(channels.names)):
            channel_item = FunctionItem(channel_descriptors[i], select_var,\
                                                (filenames, k, channels.names[i]))
            channel_menu.append_item(channel_item)
        
        # Add channel menu to main device menu
        m = SubmenuItem(k, channel_menu, dev_menu)
        dev_menu.append_item(m)
        
    H.close()

    
    dev_menu.start()
    dev_menu.join()
    
    do_plots(filenames)
    
    return
###############################################################################################


if __name__ == '__main__':

    
    if len(sys.argv)<1: print("Specify HDF5 file")
    else: main(sys.argv[1:])

