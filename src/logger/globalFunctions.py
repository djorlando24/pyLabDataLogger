#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    General purpose functions to call from datalogging scripts.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2026 Monash University
    @license GPL-3.0+
    @version 1.5.0
    @date 13/06/25

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
"""

from termcolor import cprint

def banner():
    
    stringData = ['  pyLabDataLogger - Easy data logging from USB, Serial and Network devices      ',\
                  '  @author Daniel Duke <daniel.duke@monash.edu>                                  ',\
                  '  @copyright (c) 2018-2025 D. Duke                                              ',\
                  '  @license GPL-3.0+                                                             ',\
                  '  @version 1.4.0                                                                ',\
                  '  @date 08/06/2025                                                              ',\
                  '                                                                                ',\
                  '  Multiphase Flow Laboratory                                                    ',\
                  '  Monash University, Australia                                                  ']

    cprint('='*80, 'white', 'on_blue',attrs=['bold'])
    line_number = 0
    for s_ in stringData:
        if line_number < 1: cprint(s_, 'white', 'on_blue',attrs=['bold'])
        else: cprint(s_, 'white', 'on_blue')
        line_number += 1
    cprint('='*80, 'white', 'on_blue',attrs=['bold'])
    print("")
