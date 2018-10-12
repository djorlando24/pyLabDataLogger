#!/bin/bash
for dat in /sys/bus/usb/devices/*; do
  if test -e $dat/manufacturer; then
    grep "WCH.CN" $dat/manufacturer > /dev/null && echo auto > ${dat}/power/level && echo 0 > ${dat}/power/autosuspend
  fi
done
