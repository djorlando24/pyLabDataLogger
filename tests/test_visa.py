#!/usr/bin/env python3
import pyvisa as visa
from termcolor import cprint

rm = visa.ResourceManager('@py')
cprint("Resources:",'cyan')
res=rm.list_resources()
print(res)

if len(res)==0: exit()

inst = rm.open_resource(res[0],timeout=30000)
cprint("Opening resource %s" % res[0], 'cyan')
print(inst)

q="*IDN?"
cprint(q,'green')
cprint(inst.query(q),'magenta')
