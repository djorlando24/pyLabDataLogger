pyAPT
=====
Python3 interface to Thorlabs motorized stages.


Description
-----------
This module implements a convenient interface to the motorized stages from
Thorlabs based the the APT communication protocol rev15_. The heart of this
module is the ``pyAPT.Controler`` class used for communication with the
devices itself. Howver since the *APT* protocol is used for many different
kinds of devices you should not instantiate the ``Controler`` class directely,
rather than subclassing it and overwriting the important parameters according
to your devices specifications. Have a look at ``pyAPT.MTS50`` and
``pyAPT.Z825B`` as examples for the MTS50_ and Z825B_ stages respectively.


Dependencies
------------
The actual serial communication is done via *pylibftdi*, a python wrapper for
libFTDI_, and is therefor listed as requirement in the ``setup.py`` file. Make
sure you installed libFTDI_ before running the ``setup.py`` script


Acknowledgements
----------------
This module is a fork of Shuning Bians pyAPT module published on github_ that I
ported to Python 3 and adapted it to my needs. All credits for the original
work go to him.



.. _rev15: http://www.thorlabs.de/software/apt/APT_Communications_Protocol_Rev_15.pdf
.. _MTS50: http://www.thorlabs.de/thorProduct.cfm?partNumber=MTS50/M-Z8
.. _Z825B: http://www.thorlabs.de/thorproduct.cfm?partnumber=PT1/M-Z8
.. _libFTDI: http://www.intra2net.com/en/developer/libftdi/
.. _github: https://github.com/freespace/pyAPT
