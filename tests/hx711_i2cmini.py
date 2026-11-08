import time
from i2cdriver import I2CDriver

# Connect to the I2CMini bridge
i2c = I2CDriver("/dev/cu.usbserial-DO029HWX")

# Target I2C slave address of your smart HX711 module
DEVICE_ADDRESS = 0x26

print("Reading parsed weight data from smart I2C module...")

try:
    while True:
        # Request 4 bytes (typically a float or 32-bit integer representing weight)
        data = i2c.regrd(DEVICE_ADDRESS, 4, '>i')
        success=True
        print(data)
        
        '''
        if success:
            # Interpret the data byte array (example assumes a raw 32-bit big-endian integer)
            raw_value = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
            
            # If your module uses Two's Complement for negative values:
            if raw_value & (1 << 31):
                raw_value -= (1 << 32)
                
            print(f"Raw Weight Value: {raw_value}")
        else:
            print("Failed to read from I2C bus.")
            
        time.sleep(0.5)
        '''
except KeyboardInterrupt:
    print("Measurement stopped.")

