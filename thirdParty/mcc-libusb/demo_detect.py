from os import system
from numpy import fromstring, cumsum, abs, square, linspace, uint16, mean
from time import time

def rolling_sum(a, n=4) :
    ret = cumsum(a, axis=0, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[ n - 1:]
count=0
while count<30:
    count+=1
    # read data from daq
    system('nice -n 19 ./continuous-log-usb1208HS')

    #process data
    t_s=time()
    fin=open('data.raw', 'rb')
    x=fin.read()
    y=fromstring(x,dtype=uint16)
    n=y.shape[0]/4

    y2=y.reshape((n,4))
    v=linspace(-2.5,2.5,8192)
    energy=mean(rolling_sum(square(abs(v[y2[:,0]])), n=2048))
    print time()-t_s
    if energy>=.3:
        print 'boat boat boat'
    else:
        pass
