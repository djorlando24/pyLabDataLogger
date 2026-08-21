import time
from sensirion_i2c_driver import I2cConnection
from sensirion_i2c_sen5x import Sen5xI2cDevice

import i2cdriver

class i2cdriver_interface(object):
    
    API_VERSION = 1  #: API version (accessed by I2cConnection)

    # Status codes
    STATUS_OK = 0  #: Status code for "transceive operation succeeded".
    STATUS_CHANNEL_DISABLED = 1  #: Status code for "channel disabled error".
    STATUS_NACK = 2  #: Status code for "not acknowledged error".
    STATUS_TIMEOUT = 3  #: Status code for "timeout error".
    STATUS_UNSPECIFIED_ERROR = 4  #: Status code for "unspecified error".
    
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self,exc_type, exc_val, exc_tb):
        self.close()
    
    def __init__(self,device_file="/dev/ttyUSB0"):
        self.port=device_file
        self.open()

    def description(self):
        return "i2cdriver interface"
    
    def channel_count(self):
        return None
   
    def transceive(self, slave_address, tx_data, rx_length, read_delay, timeout):
        assert type(slave_address) is int
        assert (tx_data is None) or (type(tx_data) is bytes)
        assert (rx_length is None) or (type(rx_length) is int)
        assert type(read_delay) in [float, int]
        assert type(timeout) in [float, int]
        try:
            self.dev.start(slave_address,0)
            self.dev.write(tx_data)
            self.dev.stop()
            time.sleep(read_delay)
            self.dev.start(slave_address,1)
            rxdata=self.dev.read(rx_length)
            self.dev.stop()
            return (self.STATUS_OK, None, rxdata),
        except Exception as e:
            return (self.STATUS_UNSPECIFIED_ERROR, e, ""),
    
    def open(self):
        self.dev =  i2cdriver.I2CDriver(self.port)
    
    def close(self):
        del self.dev
        

        
with i2cdriver_interface() as i2c_transceiver:
    device = Sen5xI2cDevice(I2cConnection(i2c_transceiver),0x69)

    # Print some device information
    print("Version: {}".format(device.get_version()[0]))
    print("Product Name: {}".format(device.get_product_name()[0]))
    print("Serial Number: {}".format(device.get_serial_number()[0]))

    # Perform a device reset (reboot firmware)
    device.device_reset()
    
    # Start measurement
    device.start_measurement()
    try:
        while True:
            # Wait until next result is available
            print("Waiting for new data...")
            while device.read_data_ready()[0] is False:
                time.sleep(0.1)

            # Read measured values -> clears the "data ready" flag
            values = device.read_measured_values()[0]
            print(values)

            # Access a specific value separately (see Sen5xMeasuredValues)
            #mass_concentration = values.mass_concentration_2p5.physical
            #ambient_temperature = values.ambient_temperature.degrees_celsius

            # Read device status
            status = device.read_device_status()
            print("Device Status: {}\n".format(status[0]))
            
    except KeyboardInterrupt:

        # Stop measurement
        device.stop_measurement()
        print("Measurement stopped.")