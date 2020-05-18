# Raspberry Pi control scripts

This directory contains scripts which allow pyLabDataLogger to do stuff on a Raspberry Pi using the GPIO,
for example read i2c sensors when externally triggered, and send trigger pulses out on each cycle as well.

- gpio_solenoid_loop.py 

	Use GPIO to access front-panel buttons to trigger a timed sequence of GPIO pin output events,
	to drive a solenoid. After the loop is done, query all the devices detected at startup.

- gpio_solenoid_loop_logging.py

	Use GPIO to access front-panel buttons to trigger a timed sequence of GPIO pin output events,
	to drive a solenoid. After the loop is done, log all the devices detected at startup to a file.

- gpio_ensemble_logging.py

	Use GPIO to access front-panel buttons to trigger querying and logging detected devices.
	Multiple repeated, automated logging events will happen on each button press.
        The Pi will beep when it's time to manually trigger collection of each ensemble, so
        the user can adjust an experimental setting.
	This is useful for ensemble data collection.
