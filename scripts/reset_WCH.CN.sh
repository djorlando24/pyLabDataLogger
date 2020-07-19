#!/bin/bash
#
#    Fix WCH.CN usb-to-serial adapter communications in *nix
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
#            This program is free software: you can redistribute it and/or modify
#            it under the terms of the GNU General Public License as published by
#            the Free Software Foundation, either version 3 of the License, or
#            (at your option) any later version.
#
#            This program is distributed in the hope that it will be useful,
#            but WITHOUT ANY WARRANTY; without even the implied warranty of
#            MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#            GNU General Public License for more details.
#
#            You should have received a copy of the GNU General Public License
#            along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

for dat in /sys/bus/usb/devices/*; do
  if test -e $dat/manufacturer; then
    grep "WCH.CN" $dat/manufacturer > /dev/null && echo auto > ${dat}/power/level && echo 0 > ${dat}/power/autosuspend
  fi
done
