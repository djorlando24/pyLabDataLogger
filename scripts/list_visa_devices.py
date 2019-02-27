#/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Test NI VISA support.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 29/11/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

if __name__=='__main__':
    import visa
    rm = visa.ResourceManager('@py')
    print "NI VISA resources visible:"
    rm.list_resources()
    exit()
