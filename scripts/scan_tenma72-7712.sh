#!/bin/bash
sigrok-cli -d uni-t-ut32x:conn=1a86.e008 --samples 3 -O analog -l 5
