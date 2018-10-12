"""
pyAPT - python interface to Thorlabs APT motion controllers

This is a fork of the pyAPT module written by Shuning Bian that I ported to
Python 3 and customized it to my needings. All the credits for the original
module go to him.
"""

__author__  = "Christoph Weinsheimer"
__email__   = "christoph.weinsheimer@desy.de"
__version__ = "0.2"


__all__ = ['Message',
           'Controller',
           'ControllerStatus',
           'add_PID',
           'clear_PIDs',
           'OutOfRangeError',
           'MTS50',
           'Z825B']


from pyAPT import message, controller, mts50, z825b

Message          = message.Message
Controller       = controller.Controller
ControllerStatus = controller.ControllerStatus
OutOfRangeError  = controller.OutOfRangeError
MTS50            = mts50.MTS50
Z825B            = z825b.Z825B


import pylibftdi

def add_PID(pid):
    """Add USB PID to the libftdi list

    Adds a USB PID to the list of PIDs to look for when searching for APT
    controllers

    Args:
        pid (byte): pid to add to the list
    """
    pylibftdi.USB_PID_LIST.append(pid)


def clear_PIDs():
    """Clears all USB PIDs
    """
    l = pylibftdi.USB_PID_LIST
    while len(l):
        l.pop()

"""
By default pylibftdi looks for devices with PID of 0x6001 and 0x6014 which
slows device listing and identification down when we JUST want to identify
motion controllers. So we do this little dance here.

If you are using a single class of controllers, just replace 0xfaf0 with the
controller's PID. If more than one class is being used, add each class's PID.

Note that we cannot simply do pylibftdi.USB_PID_LIST = [...] because that just
modifies pylibftdi.USB_PID_LIST, not the list used by driver.py in the
pylibftdi package.
"""

clear_PIDs()
add_PID(0xFAF0)
