#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    EXTRACT SERIAL DATA FROM LOG
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2020 LTRAC
    @license GPL-3.0+
    @version 1.4.0
    @date 08/06/25

    Multiphase Flow Laboratory
    Monash University, Australia

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    Version history:
        17/07/2020 - First version.
"""

import sys, os, glob

if __name__ == '__main__':
    
    for filename in glob.glob("capture/*.txt"):
        with open(filename,'r') as Fi:
            print(filename)
            Fo1 = open(os.path.splitext(os.path.basename(filename))[0] + '_wroteBytes.txt', 'w')
            Fo2 = open(os.path.splitext(os.path.basename(filename))[0] + '_readBytes.txt', 'w')
            mode=0
            for l in Fi:
                if 'Written data' in l:
                    l=Fi.readline()
                    mode=1
                elif 'Read data' in l:
                    l=Fi.readline()
                    mode=2
                
                if mode == 1:
                    Fo1.write(l)
                elif mode == 2:
                    Fo2.write(l)
                
            Fo1.close()
            Fo2.close()
