#!/usr/bin/env python3
import pyvisa as visa
from time import sleep
from termcolor import cprint

rm = visa.ResourceManager('@py')
cprint("Resources:",'cyan')
res=rm.list_resources()
print(res)

if len(res)==0: exit()

for data in [8,7]:
 for stop in [10,20]:
  for parity in [0,1,2]:
   for baud in [2400,4800,9600,19200,38400,56600,115200]:
    try:
        inst = rm.open_resource(res[0],timeout=500)
        #cprint("Opening resource %s" % res[0], 'cyan')
        print(inst,baud,data,parity,stop/10)
        inst.baud_rate=baud
        inst.data_bits=data
        inst.stop_bits=stop
        inst.parity=parity
        inst.flow_control=1
        #q="*IDN?"
        q=" \r\n#VR"
        #q="ID?"


        cprint('\t'+q,'green')
        r=inst.query(q)
        cprint(r,'magenta')
        if len(r) >0: break

    except visa.errors.VisaIOError:
        pass

    del inst
