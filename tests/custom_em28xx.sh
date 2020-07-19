#!/bin/bash
#
#    Load custom card driver for a special VID:PID as an em28xx device.
#
#    author Daniel Duke <daniel.duke@monash.edu>
#    copyright (c) 2020 LTRAC
#    license GPL-3.0+
#    version 1.0.0
#    date 19/07/2020
#        __   ____________    ___    ______
#       / /  /_  ____ __  \  /   |  / ____/
#      / /    / /   / /_/ / / /| | / /
#     / /___ / /   / _, _/ / ___ |/ /_________
#    /_____//_/   /_/ |__\/_/  |_|\__________/
#
#    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
#    Monash University, Australia
#
#        This program is free software: you can redistribute it and/or modify
#        it under the terms of the GNU General Public License as published by
#        the Free Software Foundation, either version 3 of the License, or
#        (at your option) any later version.
#
#        This program is distributed in the hope that it will be useful,
#        but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#        GNU General Public License for more details.
#
#        You should have received a copy of the GNU General Public License
#        along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

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
