import time
import board
import busio
import adafruit_ccs811
i2c_bus = busio.I2C(board.SCL, board.SDA)
ccs811 = adafruit_ccs811.CCS811(i2c_bus)

print("CO2: %1.0f PPM" % ccs811.eco2)
print("TVOC: %1.0f PPM" % ccs811.tvoc)
print("Temp: %0.1f C" % ccs811.temperature)
