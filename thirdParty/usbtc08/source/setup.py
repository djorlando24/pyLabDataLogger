#!/usr/bin/python
#coding=utf-8

# Setup script file for Distutils

from distutils.core import setup, Extension

setup(name = 'usbtc08',
      version = '1.8',
      description = 'Python wrapper for libusbtc08',
      author = 'Pico Technology',
      url = 'https://www.picotech.com/',
      ext_modules = [Extension('_usbtc08', sources=['usbtc08.i'], library_dirs=['/opt/picoscope/lib'], libraries=['usbtc08'])],
      py_modules = ['usbtc08'])
