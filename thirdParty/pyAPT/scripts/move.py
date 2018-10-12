#!/usr/bin/env python
"""
Usage: python move.py <serial> <distance_mm>

This program tells the specified controller to move the stage by the specified
distance in mm
"""

import time
import pylibftdi
import pyAPT
import sys

def main(args):
  if len(args)<3:
    print(__doc__)
    return 1
  else:
    serial = args[1]
    dist = float(args[2])

  try:
    with pyAPT.MTS50(serial_number=serial) as con:
      print('Found APT controller S/N',serial)
      sys.stdout.write('\tMoving stage by %.2fmm...'%(dist))
      sys.stdout.flush()
      con.move(dist)
      print('moved')
      print('\tNew position: %.2fmm'%(con.position()))
      return 0
  except pylibftdi.FtdiError as ex:
    print('\tCould not find APT controller S/N of',serial)
    return 1

if __name__ == '__main__':
  import sys
  sys.exit(main(sys.argv))

