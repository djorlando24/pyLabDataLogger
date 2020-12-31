#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    MODIFY SCALED VALUES OF PRERECORDED DATASETS
    
    Useful for applying new linear calibrations to previously collected data,
    for arbitrary voltage and current signals etc.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2021 LTRAC
    @license GPL-3.0+
    @version 1.0.4
    @date 08/12/2020
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

import sys, h5py, ast
import numpy as np
from termcolor import colored, cprint

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


#### This code block will find all valid device groups in the HDF5 file ############

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
        
###############################################################################################

# Read attribute array from device and turn it into a real python list.
def read_attr_array(b):
    s = b.decode('utf-8').replace('array(','(').replace('nan','0')
    try:
        return ast.literal_eval(s)
    except ValueError as e:
        print(s)
        raise


# Function that changes the scale, offset or units and applies the change. ####################
def change_param(filenames, dev_name, channel_idx):
    getinput = lambda prompt: Screen().input(prompt=prompt)
    
    try:
        H0 = h5py.File(filenames[0],'r')
        h5py_dev = H0[dev_name]
        names = read_attr_array(h5py_dev.attrs['channel_names'])
        scales = read_attr_array(h5py_dev.attrs['scale'])
        raw_units = read_attr_array(h5py_dev.attrs['raw_units'])
        units = read_attr_array(h5py_dev.attrs['eng_units'])
        offsets = read_attr_array(h5py_dev.attrs['offset'])
        data = h5py_dev[names[channel_idx]+'/Scaled values'][...]
        lo = np.nanmin(data)
        me = np.nanmean(data)
        hi = np.nanmax(data)
        H0.close()
        
        
        colored(dev_name+' / '+names[channel_idx], 'green', attrs=['bold'])
        print('-'*80)
        print('')
        colored("In %s" % filenames[0], 'cyan')
        colored("\tCurrent setting: scaled values = %g [%s/%s] + %g [%s]"\
               % (scales[channel_idx],units[channel_idx],raw_units[channel_idx],\
                  offsets[channel_idx],units[channel_idx]), 'cyan' )
        print("\tScaled min = %g [%s], mean = %g [%s], max = %g [%s]"\
               % (lo,units[channel_idx],me,units[channel_idx],hi,units[channel_idx]))
        print('')
        
        print("Units = %s" % units[channel_idx])
        new_units = getinput("Enter new units (ENTER for no change): ").strip()
        if len(new_units)>0: units[channel_idx] = new_units
        
        print("\nScale = %g [%s/%s]" % (scales[channel_idx],units[channel_idx],raw_units[channel_idx]))
        new_scale = getinput("Enter new scale (ENTER for no change): ")
        try:
            new_scale = float(new_scale)
            scales[channel_idx] = new_scale
        except ValueError:
            new_scale = scales[channel_idx]
            
        print("\nOffset = %g [%s]" % (offsets[channel_idx],units[channel_idx]))
        new_offset = getinput("Enter new offset (ENTER for no change): ")
        try:
            new_offset = float(new_offset)
            offsets[channel_idx] = new_offset
        except ValueError:
            new_offset = offsets[channel_idx]
        
        colored("\nThe changes will be applied to all files:",'red',attrs=['bold'])
        for f in sys.argv[1:]:
            colored('\t'+f,'red')
        
        confirm=getinput("Apply change? [y/N]: ").upper()
        
        if confirm != 'Y': return
        
        # now apply to all files
        for f in sys.argv[1:]:
            try:
                # Open file
                H1=h5py.File(f, 'a')
                h5py_dev = H1[dev_name]
                # Modify attrs
                h5py_dev.attrs['scale'] = str(scales).encode('utf-8')
                h5py_dev.attrs['offset'] = str(offsets).encode('utf-8')
                h5py_dev.attrs['eng_units'] = str(units).encode('utf-8')
                h5py_raw_dset = h5py_dev[names[channel_idx]+'/Raw values']
                h5py_dev[names[channel_idx]+'/Scaled values'].attrs['units']=new_units
                # Modify scaled values
                h5py_scaled_dset = h5py_dev[names[channel_idx]+'/Scaled values']
                h5py_scaled_dset[...] = h5py_raw_dset[...]*new_scale + new_offset
                # Close file
                H1.close()
            except KeyError as e:
                colored('In file %s:\n\t%s' % (f,e),'red')
                confirm=getinput("Press ENTER to continue...")
                
    except KeyboardInterrupt:
        pass

    
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
    
    dev_menu = ConsoleMenu("Device selection","Reading < %s >" % filenames[0],\
                           formatter=menu_format)
    
    # List devices, with channels in each
    for k in deviceFinder(H).names:
    
        #  Get all channel info
        channels = read_attr_array(H[k].attrs['channel_names'])
        scales   = read_attr_array(H[k].attrs['scale'])
        offsets  = read_attr_array(H[k].attrs['offset'])
        dtypes   = [ str(H[k+'/'+c+'/Raw values'].dtype) for c in channels ]
        
        channel_descriptors = [ '%s (orig. scale=%g, offset=%g)' % (channels[i],\
                            scales[i], offsets[i]) for i in range(len(channels)) ]
        
        # Make submenu for selecting channel
        channel_menu = ConsoleMenu("Select channel",k)
        for i in range(len(channels)):
            # Don't show non-numeric channels
            if ('S' in dtypes[i]) or ('O' in dtypes[i]):
                pass
            else:
                channel_item = FunctionItem(channel_descriptors[i], change_param,\
                                                    (filenames, k, i))
                channel_menu.append_item(channel_item)
        
        # Add channel menu to main device menu
        m = SubmenuItem(k, channel_menu, dev_menu)
        dev_menu.append_item(m)
        
    H.close()
    
    dev_menu.start()
    dev_menu.join()

    print("Committed changes to %i files." % (len(filenames)))

    return
###############################################################################################


if __name__ == '__main__':
    
    main(sys.argv[1:])

