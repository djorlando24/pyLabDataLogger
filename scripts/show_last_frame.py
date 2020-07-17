#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Show just last frame of Video capture in HDF file.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2020 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 13/07/2020
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
"""
    
import sys
import h5py
import numpy as np
import matplotlib.pyplot as plt

if __name__=='__main__':
	H=h5py.File(sys.argv[1],'r')
	Dev=H['Video capture card (video stream)']
	Frames=Dev.keys() 
	LastFrame = [ f for f in Frames if 'frame' in f ][-1]
	Timestamps = Dev['timestamp']
	LastTimestamp = Timestamps[-1]
	ImageData = Dev[LastFrame][...]
	ImageData = np.fliplr(np.flipud(ImageData))
	fig=plt.figure()
	plt.suptitle(sys.argv[1])
	plt.title('%s @ %s' % (LastFrame,LastTimestamp))
	plt.imshow(ImageData)
	H.close()
	plt.show()
