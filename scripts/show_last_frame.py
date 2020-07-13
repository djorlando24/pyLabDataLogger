#!/usr/bin/env python
# Show just last frame of Video capture in HDF file.
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
