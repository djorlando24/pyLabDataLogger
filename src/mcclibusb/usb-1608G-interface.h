/*
    Measurement Computing USB device support functions
    MCC USB1608G series devices
    For interfacing Python to libmccusb and usb-1608G
    based on the mcc-libusb driver by Warren J. Jasper

    #include this code in usb-1608G.c provided by libmccusb
    to add required support and interface functions. 

    the Python interface will expect the following methods:
        pyudev_t detect_device(bool quiet)
        int activate_device(pyudev_t pyudev, bool quiet)
    
    The pyudev_t struct contains a PyObject* which is a PyCapsule
    containing the libusb_device_handle pointer, followed by
    any required flags or parameters to pass.

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 14/11/2018
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
*/

#include "Python.h"

#define FALSE 0
#define TRUE 1

// A struct that can hold all the information required to pass to any function so it can
// talk to the device.
typedef struct {
    PyObject* udev_capsule;
    _Bool usb1608GX_2AO;
    int model;
} pyudev_t;


// Device detection - determine exact model number and open libusb udev pointer
pyudev_t detect_device(_Bool quiet) {
  
  libusb_device_handle *udev = NULL;
  udev = NULL;
  int usb1608GX_2AO = FALSE;
  pyudev_t pyudev = {NULL, FALSE, 0};
  
  int ret = libusb_init(NULL);
  if (ret < 0) {
    printf("\tlibusb_init: Failed to initialize libusb\n");
    return pyudev;
  }

   

  if ((udev = usb_device_find_USB_MCC(USB1608G_PID, NULL))) {
    if (!quiet) printf("\tdetected USB 1608G\n");  
    pyudev.model = 1;
  } else if ((udev = usb_device_find_USB_MCC(USB1608GX_PID, NULL))) {
    if (!quiet) printf("\tdetected USB 1608GX\n");
    pyudev.model = 2;
  } else if ((udev = usb_device_find_USB_MCC(USB1608GX_2AO_PID, NULL))) {
    if (!quiet) printf("\tdetected USB 1608GX_2AO\n");
    usb1608GX_2AO = TRUE;
    pyudev.model = 3;
  } else if ((udev = usb_device_find_USB_MCC(USB1608G_OLD_PID, NULL))) {
    if (!quiet) printf("\tdetected USB 1608G\n");
    pyudev.model = 4;
  } else if ((udev = usb_device_find_USB_MCC(USB1608GX_OLD_PID, NULL))) {
    if (!quiet) printf("\tdetected USB 1608GX\n");
    pyudev.model = 5;
  } else if ((udev = usb_device_find_USB_MCC(USB1608GX_2AO_OLD_PID, NULL))) {
    if (!quiet) printf("\tdetected USB 1608GX_2AO\n");
    usb1608GX_2AO = TRUE;
    pyudev.model = 6;
  } else {
    if (!quiet) printf("Failure, did not find a USB 1608G series device!\n");
    return pyudev;
  }

  // Make a python capsule for udev pointer
  PyObject *udev_capsule = PyCapsule_New((void*) udev, "udev", NULL);
  pyudev.udev_capsule = udev_capsule;
  pyudev.usb1608GX_2AO = usb1608GX_2AO;
  
  return pyudev;

}


// Device activation & setup
int activate_device(pyudev_t pyudev, _Bool quiet) {

  // Unpack pyudev struct contents
  libusb_device_handle *udev = PyCapsule_GetPointer(pyudev.udev_capsule, "udev");
  int usb1608GX_2AO = pyudev.usb1608GX_2AO;
  
  // Init vars
  struct tm calDate;
  float table_AIN[NGAINS_1608G][2];
  float table_AO[NCHAN_AO_1608GX][2];
  int i;

  // Init device
  printf("\t");
  usbInit_1608G(udev);  

  //print out the wMaxPacketSize.  Should be 512
  if (!quiet) printf("\twMaxPacketSize = %d\n", usb_get_max_packet_size(udev,0));

  usbBuildGainTable_USB1608G(udev, table_AIN);
  for (i = 0; i < NGAINS_1608G; i++) {
    if (!quiet) printf("\tGain: %d   Slope = %f   Offset = %f\n", i, table_AIN[i][0], table_AIN[i][1]);
  }

  if (usb1608GX_2AO) {
    usbBuildGainTable_USB1608GX_2AO(udev, table_AO);
    printf("\n");
    for (i = 0; i < NCHAN_AO_1608GX; i++) {
      if (!quiet) printf("\tVDAC%d:    Slope = %f    Offset = %f\n", i, table_AO[i][0], table_AO[i][1]);
    }
  }

  usbCalDate_USB1608G(udev, &calDate);
  if (!quiet) printf("\n");
  if (!quiet) printf("\tMFG Calibration date = %s\n", asctime(&calDate));
 
  /*char* serial[9];
  usbGetSerialNumber_USB1608G(udev, serial);
  printf("Serial number = %s\n", serial);
  
  uint16_t version = 0;
  usbFPGAVersion_USB1608G(udev, &version);
  printf("FPGA version %02x.%02x\n", version >> 0x8, version & 0xff);
  */
  return 1;
}
