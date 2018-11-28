#!/bin/bash
sudo avrdude -c linuxspi -p t45 -P /dev/spidev0.0 -U flash:w:$1
