#!/usr/bin/env python
import usbtmc
vid,pid = (0x0957,0x0407)
instr =  usbtmc.Instrument(vid,pid)
print(instr.ask("*IDN?"))

