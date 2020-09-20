#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    Show just last frame of Video capture in HDF file.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @version 1.0.1
    @date 19/07/2020
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

    Version history:
        13/07/2020 - First version.
        18/07/2020 - Bug fixes
        19/07/2020 - allow overwrite, colour text.
"""
    
import sys, os, shutil
import h5py
import tqdm
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from termcolor import cprint

IMAGE_EXTN = 'jpg'

if __name__=='__main__':

    if len(sys.argv) < 2:
        print("Usage: %s hdf5-file-name")
        exit(1)

    # Open File
    H=h5py.File(sys.argv[1],'r')
    
    # Find all devices containing image data type
    cprint("Scanning for images in HDF5 file...",'cyan')
    videoDevices = [ g for g in H.values() if np.any([ 'IMAGE_SUBCLASS' in g.values()[n].attrs.keys() for n in range(len(g.keys()))])  ]
    
    # Loop thru all devices
    for Dev in videoDevices:
        Timestamps = Dev['timestamp']
        output_dir = "%s_%s" % (os.path.splitext(sys.argv[1])[0], Dev.name.replace('/',''))
        print("Saving %s %s \n\t-> %s" % (sys.argv[1],Dev.name,output_dir))
        
        # Overwrite?
        if os.path.exists(output_dir):
            print("Overwriting %s" % output_dir)
            shutil.rmtree(output_dir)

        # Make dir to save to
        os.mkdir(output_dir)

        # Loop thru each image
        all_frames = [ fr for fr in Dev.values() if 'IMAGE_SUBCLASS' in fr.attrs.keys() ]
        for i in tqdm.tqdm(range(len(all_frames))):
            frame = all_frames[i]
            frame_name = os.path.basename(frame.name)
            n = int(frame_name.split('_')[-1]) - 1 # frame usually starts at 1 not 0
            if (n<len(Timestamps)) and (n>=0): ts = Timestamps[n]
            else: ts = "noTimestamp"
            output_name = "%s_%s.%s" % (frame_name, ts, IMAGE_EXTN)
            full_path = output_dir+'/'+output_name
            
            # Load image array, flip around to the right way up.
            im = Image.fromarray(np.fliplr(np.flipud(frame[...])))
            # Save image
            im.save(full_path)
            
        print("")
    
    cprint("Done.",'cyan')
            
            
            
        
        
        
    
