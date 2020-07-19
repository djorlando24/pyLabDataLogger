#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    READ DIAL GAUGE IMAGE
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-20 LTRAC
    @license GPL-3.0+
    @version 1.0.0
    @date 22/05/2020
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

import h5py
import sys, os, subprocess, shutil
import matplotlib.pyplot as plt
import numpy as np
from joblib import Parallel, delayed
#import scipy.interpolate

if __name__ == '__main__':
    
    ### Geometry ###################################################
    # Define dial points and corresponding engineering values
    # They should be on a common arc with the center at c
    # Don't use the zero point, it's often not actually zero
    dial_min = 0. # minimum value allowed
    eng_units = 'kPa'
    radius_ratio = 0.85 # make arc inside any markings
    
    '''
    c=(272,328) # center
    p0=(296,162,  10.) # calibration point @ 10 kPa
    p1=(381,450,  60.) # calibration point @ 60 kPa
    '''
    '''
    c=(269,341) # center
    p0=(285,174,  10.) # calibration point @ 10 kPa
    p1=(382,454,  60.) # calibration point @ 60 kPa
    radius_ratio = 0.8 # make arc inside any markings
    '''
    '''
    c=(294,352)
    p0=(314,184,  10.) # calibration point @ 10 kPa
    p1=(408,466,  60.) # calibration point @ 60 kPa
    '''
    '''
    c=(267,341)
    p0=(285,172, 10.) # calibration point @ 10 kPa
    p1=(381,455, 60.)# calibration point @ 60 kPa
    '''
    '''
    c=(295,349)
    p0=(312,185,10.)
    p1=(407,466,60.)
    '''
    '''
    c=(296,352)
    p0=(317,181,10.)
    p1=(409,477,60.)
    '''
    '''
    c=(295,351)
    p0=(318,183,10.)
    p1=(407,459,60.)
    radius_ratio = 0.78
    '''
    '''
    c=(297,343)
    p0=(313,179,10.)
    p1=(410,456,60.)
    '''
    '''
    c=(312,350)
    p0=(333,183,10.)
    p1=(423,466,60.)
    '''
    '''
    c=(259,338)
    p0=(270,166,10.)
    p1=(381,454,60.)
    '''
    c=(272,348)
    p0=(293,177,10.)
    p1=(384,471,60.)
    
    # smoothing kernel for denoising the interpolated pixel values
    kern = np.hanning(25,)
    kern /= np.sum(kern)
    
    if c is not None:
        # find arc radii
        r0 = np.sqrt( (p0[0] - c[0])**2 + (p0[1] - c[1])**2 )
        r1 = np.sqrt( (p1[0] - c[0])**2 + (p1[1] - c[1])**2 )
        radius = radius_ratio*0.5*(r0+r1) # take mean
        
        # find arc angles
        t0 = np.arctan2( p0[0] - c[0], p0[1] - c[1] )
        t1 = np.arctan2( p1[0] - c[0], p1[1] - c[1] )
        if t0>t1: t0 -= 2*np.pi
        
        # define arc
        theta = np.linspace(0,2*np.pi,1440)
        arc_y = c[0] + radius*np.sin(theta)
        arc_x = c[1] + radius*np.cos(theta)
        
        # map angle to engineering value
        def dialValue(th_rad):
            slope = (p1[2] - p0[2])/(t1 - t0)
            offset = slope*t1 - p1[2]
            return np.mod(slope*th_rad - offset - dial_min, slope*2*np.pi) + dial_min
    
    #fig=plt.figure()
    #plt.plot(theta, dialValue(theta))
    #plt.show();exit()
    
    ### Read images #################################################
    
    # Open file
    H = h5py.File(sys.argv[1],'a')
    
    # Find image-based data sets
    image_datasets = []
    for dev in H:
        k = [ k.split('_')[0] for k in H[dev].keys() ]
        if ('frame' in k) or ('img' in k) or ('image' in k):
            image_datasets.append(dev)

    # Select an image-based dataset
    if len(image_datasets)==0:
        raise RuntimeError("No image data found.")
    elif len(image_datasets)==1:
        dev = image_datasets[0]
    else:
        print("Multiple image devices detcted. Please select:")
        for n in range(len(image_datasets)):
            print("%i) %s" % (n,image_datasets[n]))
        n=-1
        while (n<0) or (n>=len(image_datasets)):
            try:
                n=int(input('> '))
            except ValueError:
                n=-1
        dev = image_datasets[n]
    print("Selected device: "+dev)
    
    # Define a list of images
    images = [ H[dev][k] for k in H[dev].keys() if k != 'timestamp' and k != 'Postprocessed values']
    
    # Load a sample image to make alignment
    if c is None:
        fig=plt.figure()
        plt.imshow(np.flip(np.array(images[0]),axis=-1))
        plt.show()
        print("Exiting to enter alignment values")
        exit()
    
    # convert images to 4d numpy array
    print("Converting image data to array...")
    all_images = np.flip(np.stack(images),axis=-1).astype(np.float32)
    print(all_images.shape)
    
    # Convert RGB images to work on feature detection
    all_images /= 256.
    mono_images = np.nanmean(all_images,axis=-1) # make 3d monochrome array.
    I = 1 - mono_images # Invert
    #I -= np.mean(I,axis=0) # Remove mean
    I[I<0]=0 # Mask low intensity regions
    
    ### Find the needle in the haystack #################################################
    def process_frame(I, original_image, arc_x, arc_y, kern, frame_number, img_path=''):
    
        # Nearest neighbour interpolation onto arc
        arc_I0 = np.array([ I[int(arc_y[i]),int(arc_x[i])] for i in range(len(theta)) ])
        arc_I = np.convolve(arc_I0,kern,'same') # smooth, to find larger peaks
    
        # Find peak, half width and middle of peak
        i_peak = np.where(arc_I == np.nanmax(arc_I))[0][0]
        i_half = [i_peak, i_peak]
        for j in range(2):
            while (arc_I[i_half[j]] >= 0.5*np.nanmax(arc_I)) and (i_half[j]>0) and (i_half[j]<len(arc_I)-1):
                if j==0: i_half[j] -= 1
                else: i_half[j] += 1
        i_middle = np.mean(np.array(i_half).astype(np.float))
        theta_middle = np.interp(i_middle, np.arange(len(arc_I)), theta)
        
        
        # find actual value
        dv = dialValue(theta_middle)
    
        # Draw
        fig=plt.figure()
        plt.suptitle(sys.argv[1])
        plt.title(r'$\theta = %f^{\circ}$, value = %f %s' % (theta_middle*180/np.pi,dv,eng_units))
        plt.imshow(original_image)
        plt.plot(arc_x,arc_y,c='w',lw=1,alpha=.9)
        needle_y = c[0] + np.arange(2*radius)*np.sin(theta_middle)
        needle_x = c[1] + np.arange(2*radius)*np.cos(theta_middle)
        plt.plot(needle_x,needle_y,c='w',lw=2,alpha=.9)
        plt.savefig('%s%06i.png' % (img_path,frame_number))
        del fig
        
        #plt.show(); exit() # debug
        return dv
    
    # Make path to store images
    img_path = os.path.splitext(sys.argv[1])[0]+'/'
    try:
        os.mkdir(img_path)
    except FileExistsError as e:
        print("Warning: image directory already exists")
    
    # run parallel
    values = Parallel(n_jobs=-1, verbose=10)(delayed(process_frame)(I[i,...], all_images[i,...],\
                                               arc_x, arc_y, kern, i, img_path) for i in range(I.shape[0]))
    
    # write back
    print("Writing to hdf5 file")
    dest_dset = 'Postprocessed values'
    if dest_dset in H[dev]:
        print("   (overwriting previous)")
        del H[dev][dest_dset]
    dd = H[dev].create_dataset(dest_dset, data= np.array(values), compression='gzip')
    dd.attrs['units']=eng_units
    dd.attrs['method']='dial gauge image analysis'
    dd.attrs['center']=str(c)
    dd.attrs['points']=str(p0)+' '+str(p1)
    dd.attrs['dial_min']=dial_min
    dd.attrs['radius_ratio']=radius_ratio

    H.close()     # Close file
    
    ### Make movie #################################################
    movie_file = '%s.mp4' % os.path.splitext(sys.argv[1])[0]
    subprocess.call(['ffmpeg','-y','-i','%s%%6d.png' % img_path, '-c:v','libx264', '-r','25', '-pix_fmt','yuv420p','-preset','medium', movie_file])
    if os.path.exists(movie_file):
        shutil.rmtree(img_path)
    print("Saved movie to %s and removed images from %s" % (movie_file, img_path))
    
    ### Show plot(s) #################################################
    
    fig=plt.figure()
    plt.plot(values,marker='o')
    plt.title(sys.argv[1])
    plt.xlabel('Frame #')
    plt.ylabel('Measured value (%s)' % eng_units)
    plt.show()
    print("Done.")
    
    
    # Debugging plots
    '''
    fig=plt.figure()
    ax=fig.add_subplot(221)
    ph=ax.imshow(I[-1,...])
    ax.plot(arc_x,arc_y,c='w',lw=1,alpha=.5)
    ax.plot(needle_x,needle_y,c='w',lw=2,alpha=.5)
    plt.colorbar(ph)
    
    ax=fig.add_subplot(222)
    ph=ax.imshow(all_images[-1,...])
    ax.plot(arc_x,arc_y,c='w',lw=1,alpha=.9)
    ax.plot(needle_x,needle_y,c='w',lw=2,alpha=.9)
    plt.colorbar(ph)
    
    ax=fig.add_subplot(223)
    ax.plot(theta*180/np.pi, arc_I0, lw=1)
    ax.plot(theta*180/np.pi, arc_I, lw=1)
    plt.axvline(theta_middle*180/np.pi,c='k',ls='--')
    
    plt.show()
    '''
    
