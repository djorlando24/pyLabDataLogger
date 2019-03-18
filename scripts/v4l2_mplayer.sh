#!/bin/bash
# Get info on video devices
for VIDEO_DEVICE in /dev/video* ; do echo -e "\n\n$VIDEO_DEVICE\n" ; v4l2-ctl --device=$VIDEO_DEVICE --list-inputs ; done
# play stream
mplayer tv://device=/dev/video0 -tv norm=NTSC:width=720:height=480
