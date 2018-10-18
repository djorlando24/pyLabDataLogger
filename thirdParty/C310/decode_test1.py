#!/usr/bin/env python
import sys

if len(sys.argv)<2: out = sys.stdout
else: out = open(sys.argv[1],'w')

last=None
with open('ttyUSB0.log','r') as f:
    i=0
    for l in f.readlines():
        if '>' in l:
            if last == 1: out.write('\n') # Break between RECV & SEND blocks
            out.write( "%04i RECV `%s'" % (i, l.replace('> ','').strip()))
            last=0
        elif '<' in l:
            if last == 0: out.write('\n') # Break between RECV & SEND blocks
            out.write( "%04i SEND `%s'" % (i, l.replace('< ','').strip()))
            last=1
        else:
            out.write( "%04i ???? `%s'" % (i, l.strip()))
            last=None
        
        if '0x' in l:
            j=l.index('0x')
            s=l[j:].strip().split(' ')[0] # hex as string
            out.write("\t\t")
            out.write("%03i" % int(s,0)) # as int
            out.write("\t")
            out.write("%s" % bytearray.fromhex(s[2:])) # as int

        out.write('\n')
        i+=1
        out.flush()

if len(sys.argv)>=2: 
    out.close()
    print "Wrote to %s." % sys.argv[1]


