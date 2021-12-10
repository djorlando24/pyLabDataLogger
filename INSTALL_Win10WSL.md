# Installation instructions for pyLabDataLogger using WSL2 on Windows 10

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2019-2021 LTRAC
    @license GPL-3.0+
    @version 1.1.3
    @date 11/12/2021
        __   ____________    ___    ______    
       / /  /_  ____ __  \  /   |  / ____/    
      / /    / /   / /_/ / / /| | / /         
     / /___ / /   / _, _/ / ___ |/ /_________ 
    /_____//_/   /_/ |__\/_/  |_|\__________/ 

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    This software searches for sensors and data acquisition devices
    over a range of communication protocols and logs them to a local file.


*These instructions are relevant for Ubuntu 20 on Windows 10.*

## 1. Install Windows Subsystem for Linux:

- Right click on Start, select Windows Powershell (Admin), enter credentials
- Type `wsl --install` 
- Reboot
- Log back in and wait for installation to complete
- Create a Ubuntu username and password
- Right click on Start, select Windows Powershell (Admin), run `wsl --update`
- Open the Ubuntu terminal:
	- Run `sudo apt update && sudo apt-get upgrade` to update the Ubuntu install.
    - Run `sudo apt install build-essential flex bison libssl-dev libelf-dev libncurses-dev autoconf libudev-dev libtool

## 2. Install Python and dependencies

Just follow these commands as required for any Linux:

```
	sudo apt install libhidapi-dev libhidapi-hidraw0 libhidapi-libusb0 libusb-1.0-0 libusb-1.0-0-dev python3 python3-dev libftdi1 libftdi-dev
	sudo apt install cython3 python3-numpy python3-matplotlib python3-pip python3-gi-cairo
	sudo pip3 install natsort h5py tqdm termcolor pyusb pylibftdi libscrc pygobject
```

## 3. Install WSL specific files

- Add the Microsoft repoositories for Ubuntu 20
	```
	# Install repository configuration
	curl -sSL https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/microsoft-prod.list

	# Install Microsoft GPG public key
	curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc

	# Update package index files
	sudo apt-get update
	```
	
- Run `sudo apt install hwdata linux-tools-generic `
- find the linux-tools directory: `ls -d /usr/lib/linux-tools/*` (the asterisk is `uname -r`)
- Copy this directory and add it to the secure_path using `sudo visudo`
	`Defaults        secure_path="/usr/lib/linux-tools/5.4.0-91-generic:/usr/local/sbin:/`...
- In Powershell, run `wsl --update`

- Now to add graphics support,
	-Download [https://sourceforge.net/projects/vcxsrv] and install.
	-Go to start menu and activate *XLaunch*.
	-add this line to ~/.profile in WSL:
	```
		export DISPLAY="$(grep nameserver /etc/resolv.conf | sed 's/nameserver //'):0"
	```
	-Close and re-open the Ubuntu window. Now you can have graphics.

## 4. Add support for USB-Serial adapters to WSL

See *[https://askubuntu.com/questions/1373910/ch340-serial-device-doesnt-appear-in-dev-wsl]*

```
	sudo apt install build-essential flex bison libssl-dev libelf-dev dwarves libncurses-dev`
	git clone https://github.com/microsoft/WSL2-Linux-Kernel.git
	cd WSL2-Linux-Kernel
	make menuconfig KCONFIG_CONFIG=Microsoft/config-wsl
```
	
	Go to Device Drivers -> USB Support -> USB Serial Converter support then enable your drivers in here.

```	
	make KCONFIG_CONFIG=Microsoft/config-wsl -j8
	cp arch/x86/boot/bzImage /mnt/c/Users/<your-user-name-here>/wsl_kernel
```
	
	Create a file in your Windows user directory called .wslconfig and paste this into it:

```
	[wsl2]
	kernel = C:\\Users\\<your-user-name-here>\\wsl_kernel
```	
	Shut down WSL with wsl --shutdown in a Windows command prompt.


## 5. Install sigrok-cli in WSL

- Install dependencies: ` sudo apt install check gobject-introspection libgirepository1.0-dev pkg-config sdcc libzip-dev python-gi-dev libgtk2.0-dev libglibmm-2.4-dev doxygen swig`
- Download source from [https://sigrok.org/wiki/Downloads]
- build each package in order with `./configure python=python3 && make -j8 && sudo make install`


## 6. Install USBIPD software

- Go to [https://github.com/dorssel/usbipd-win/releases/tag/v1.2.0]
- Install usbipd-win 1.2.0
- Reboot Windows

## 7. Install pyLabDataLogger in WSL

```
	git clone https://github.com/djorlando24/pyLabDataLogger.git
```

Then follow the instructions in Install.md for "building on Linux".

## 8. Find and attach your USB devices to WSL.
 
- Open a Windows Admin Powershell
- Run `usbipd wsl list`
- Get the BUSIDs of the device you wish to use, for example:
	```	PS C:\Windows\system32> usbipd wsl list
		BUSID  DEVICE                                                        STATE
		1-1    USB-SERIAL CH340 (COM3)                                       Not attached
	```
- Attach the device. In the Powershell:
	`usbipd wsl attach -b X-Y`  where X-Y is the BUSID from above.
	
	- In Linux, `lsusb` should show the device now:
	```
		> usbipd wsl list
		BUSID  DEVICE                                                        STATE
		1-1    USB-SERIAL CH340                                              Attached - Ubuntu
		1-2    Unknown Device #1                                             Not attached
		1-4    USB Audio Device, USB Input Device                            Not attached
		2-1    USB Input Device                                              Not attached
		2-2    USB Input Device                                              Not attached
		4-10   Goodix Moc Fingerprint                                        Not attached
		4-11   USB Video Device                                              Not attached
		4-14   Intel(R) Wireless Bluetooth(R)                                Not attached
	```

	- You can confirm attachment in the Windows Powershell via `usbipd wsl list`
	```
		$ lsusb
		Bus 001 Device 002: ID 1a86:7523 QinHeng Electronics HL-340 USB-Serial adapter
	```

- A note about some sigrok devices that flash the firmware - the USB connection can drop and reconnect.
	When this happens, usbipd will lose the device and Win10 will grab it back.
	Just run the `usbipd wsl attach` command again.

## 9. Run pyLabDataLogger

- In the Ubuntu terminal, go to pyLabDataLogger directory
- Run `python3 scripts/detect_usb_devices.py` to see if USB device is picked up.
- Run `python3 scripts/log_usb_devices.py` to do a logging loop to HDF5.
