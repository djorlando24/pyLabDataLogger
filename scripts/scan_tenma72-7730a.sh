#!/bin/bash
sigrok-cli -d tenma-72-7730:conn=1a86.e008 --scan
sigrok-cli -d tenma-72-7730:conn=1a86.e008 --samples 1 -O analog -l 5
