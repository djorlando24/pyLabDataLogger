#!/usr/bin/env python

# NOTE! This code should not be used as the basis for a real
# smoke or fire detector, or in life-critical situations. It's
# for fun/novelty use only, so bear that in mind while using it.

import time
import datetime
from max30105 import MAX30105, HeartRate

max30105 = MAX30105()
max30105.setup(leds_enable=3)


max30105.set_led_pulse_amplitude(1, 0.0)
max30105.set_led_pulse_amplitude(2, 0.0)
max30105.set_led_pulse_amplitude(3, 12.5)

max30105.set_slot_mode(1, 'red')
max30105.set_slot_mode(2, 'ir')
max30105.set_slot_mode(3, 'green')
max30105.set_slot_mode(4, 'off')

hr = HeartRate(max30105)

# Smooths wobbly data. Increase to increase smoothing.
mean_size = 20

# Compares current smoothed value to smoothed value x
# readings ago. Decrease this to increase detection
# speed.
delta_size = 10

# The delta threshold at which a change is detected.
# Decrease to make the detection more sensitive to
# fluctuations, increase to make detection less
# sensitive to fluctuations.
threshold = 10

data = []
means = []

timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")

file_dir = "/home/pi/"  # Where to save log file.

print("""
NOTE! This code should not be used as the basis for a real
smoke or fire detector, or in life-critical situations. It's
for fun/novelty use only, so bear that in mind while using it.

This example uses the green LED to detect the amount of green
light reflected back to the sensor. An increase in relected
light should correlate to an increase in particles in front of
the sensor.

Any movement of objects close to the sensor is likely to also
trigger detection of a change.

Values are printed to the terminal and to a datestamped text
file in the directory file_dir.
""")

delay = 10

print("Starting readings in {} seconds...\n".format(delay))
time.sleep(delay)

try:
    with open(file_dir + timestamp + ".txt", "w") as f:
        f.write("time,green,mean,delta,change_detected,temp\n")
        while True:
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            samples = max30105.get_samples()
            if samples is not None:
                f.write(timestamp + ",")
                r = samples[2] & 0xff
                d = hr.low_pass_fir(r)
                data.append(d)
                if len(data) > mean_size:
                    data.pop(0)
                mean = sum(data) / float(len(data))
                means.append(mean)
                if len(means) > delta_size:
                    delta = means[-1] - means[-delta_size]
                else:
                    delta = 0
                if delta > threshold:
                    detected = True
                else:
                    detected = False
                print("Value: {:.2f} // Mean: {:.2f} // Delta: {:.2f} // \
Change detected: {}".format(d, mean, delta, detected))
                f.write("{:.2f},".format(d))
                f.write("{:.2f},".format(mean))
                f.write("{:.2f},".format(delta))
                f.write("{},".format(detected))
                time.sleep(0.05)
                temp = max30105.get_temperature()
                f.write("{:.2f}\n".format(temp))
                time.sleep(0.05)

except KeyboardInterrupt:
    f.close()
    pass

