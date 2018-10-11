"""
Z825B - controller subclass for the Thorlabs Z825B stage
"""

from .controller import Controller

class Z825B(Controller):
    """
    Z825B - controller subclass for the Thorlabs Z825B stage
    """

    def __init__(self, serial_number=None, label=None, scale_correction=1.0):
        """Constructor

        Args:
            serial_number (str): S/N of the device
            label (str): optional name of the device
            scale_correction (float): correction factor for position scale
        """

        super(Z825B, self).__init__(serial_number, label)

        # actually 2.6 mm/s but ripples appear above 2.3 mm/s
        self.max_velocity = 2.2
        # actually 4.0 mm/s/s but be more conservative for safety
        self.max_acceleration = 3.5
     
     
        # From Thorlabs APT specification rev.14
        enccnt                  = int(34304 * scale_correction)
        T                       = 2048/6e6
        self.position_scale     = enccnt
        self.velocity_scale     = enccnt * T * 65536
        self.acceleration_scale = enccnt * T * T * 65536
     
        self.linear_range = (0,25)

