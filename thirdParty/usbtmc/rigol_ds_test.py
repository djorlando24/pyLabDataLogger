#!/usr/bin/env python
import usbtmc
vid,pid = (v,p)
instr =  usbtmc.Instrument(vid,pid)
print(instr.ask("*IDN?"))

