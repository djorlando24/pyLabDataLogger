#!/bin/bash

# Load custom card driver for a special VID:PID as an em28xx device.
# Daniel Duke
# <daniel.duke@monash.edu>

# Here, I have a Roxio device with id 1b80:e31d that em28xx doesn't know about.
# I will force a card type, reload the driver, then tell the driver to accept the VID:PID.

echo "Unplug device"
read

sudo rmmod em28xx_v4l
sudo rmmod em28xx_dvb
sudo rmmod em28xx_rc
sudo rmmod em28xx


sudo insmod /lib/modules/4.15.0-70-generic/kernel/drivers/media/usb/em28xx/em28xx.ko card=9
sudo insmod /lib/modules/4.15.0-70-generic/kernel/drivers/media/usb/em28xx/em28xx-v4l.ko
sudo insmod /lib/modules/4.15.0-70-generic/kernel/drivers/media/usb/em28xx/em28xx-dvb.ko
sudo insmod /lib/modules/4.15.0-70-generic/kernel/drivers/media/usb/em28xx/em28xx-rc.ko

sudo sh -c "echo 1b80 e31d > /sys/bus/usb/drivers/em28xx/new_id"

echo "Plug in device"
read

dmesg
echo
ls /dev/video*
