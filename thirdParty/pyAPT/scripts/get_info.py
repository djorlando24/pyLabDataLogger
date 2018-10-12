#!/usr/bin/env python
"""
Usage: python get_info.py [<serial>]

Gets the controller information of all APT controllers, or the one specified

DD - print firmware as hex, note that S/N from info() method is not right
"""

import pyAPT

from runner import runner_serial

@runner_serial
def info(serial):
  with pyAPT.Controller(serial_number=serial) as con:
    info = con.info()
    print('\tController info:')
    labels=['S/N','Model','Type','Firmware Ver', 'Notes', 'H/W Ver',
            'Mod State', 'Channels']

    for idx,ainfo in enumerate(info):
      if ('Firmware' in labels[idx]):
          print('\t%12s: %s'%(labels[idx], ainfo.encode('hex')))
      else:
          if type(ainfo) == bytes: ainfo = ainfo.decode('latin-1')
          print('\t%12s: %s'%(labels[idx], ainfo))

if __name__ == '__main__':
  import sys
  sys.exit(info())



