"""
MTS50 - controller subclass for the Thorlabs MTS50/M-Z8 stage
"""

from .controller import Controller

class MTS50(Controller):
    """
    MTS50 - controller subclass for the Thorlabs MTS50/M-Z8 stage
    """

    def __init__(self, serial_number=None, label=None, scale_correction=1.0):
        """Constructor

        Args:
            serial_number (str): S/N of the device
            label (str): optional name of the device
            scale_correction (float): correction factor for position scale
        """

        super(MTS50, self).__init__(serial_number, label)
     
        self.max_velocity = 2.2
        self.max_acceleration = 4.0
     
     
        # From Thorlabs APT specification rev.14
        enccnt = int(34304 * scale_correction)
        T = 2048/6e6
        self.position_scale = enccnt
        self.velocity_scale = enccnt * T * 65536
        self.acceleration_scale = enccnt * T * T * 65536
     
        self.linear_range = (0,50)

