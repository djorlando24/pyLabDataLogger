/*
    Measurement Computing USB device support functions
    MCC USB1608G series devices
    For interfacing Python to libmccusb and usb-1608G
    based on the mcc-libusb driver by Warren J. Jasper

    #include this code in usb-1608G.c provided by libmccusb
    to add required support and interface functions. 

    The pyudev_t struct contains a PyObject* which is a PyCapsule
    containing the libusb_device_handle po(char*)inter, followed by
    any required flags or parameters to pass.

    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.0.1
    @date 23/11/2018
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
    int n_channels;
    int n_samples;
    float table_AIN[NGAINS_1608G][2];
    float table_AO[NCHAN_AO_1608GX][2];
    uint16_t *buffer;
    ScanList list[NCHAN_1608G];
} pyudev_t;


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Device detection - determine exact model number and open libusb udev pointer
pyudev_t detect_device(_Bool quiet) {
  
  libusb_device_handle *udev = NULL;
  udev = NULL;
  int usb1608GX_2AO = FALSE;
  pyudev_t pyudev = {NULL, FALSE, 0, 0, 0, {{0}}, {{0}}, NULL};
  
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

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Device activation & setup
pyudev_t activate_device(pyudev_t pyudev, _Bool quiet) {

  // Unpack pyudev struct contents
  libusb_device_handle *udev = PyCapsule_GetPointer(pyudev.udev_capsule, "udev");
  int usb1608GX_2AO = pyudev.usb1608GX_2AO;
  
  // Init vars
  struct tm calDate;
  //float table_AIN[NGAINS_1608G][2];
  //float table_AO[NCHAN_AO_1608GX][2];
  int i;

  // Init device
  printf("\t");
  usbInit_1608G(udev);  

  //print out the wMaxPacketSize.  Should be 512
  if (!quiet) printf("\twMaxPacketSize = %d\n", usb_get_max_packet_size(udev,0));

  // Gain tables
  usbBuildGainTable_USB1608G(udev, pyudev.table_AIN);
  for (i = 0; i < NGAINS_1608G; i++) {
    if (!quiet) printf("\tGain: %d   Slope = %f   Offset = %f\n", i, pyudev.table_AIN[i][0], pyudev.table_AIN[i][1]);
  }

  if (usb1608GX_2AO) {
    usbBuildGainTable_USB1608GX_2AO(udev, pyudev.table_AO);
    for (i = 0; i < NCHAN_AO_1608GX; i++) {
      if (!quiet) printf("\tVDAC%d:    Slope = %f    Offset = %f\n", i, pyudev.table_AO[i][0], pyudev.table_AO[i][1]);
    }
  }

  
  if (!quiet) {
    usbCalDate_USB1608G(udev, &calDate);
    printf("\tMFG Calibration date = %s", asctime(&calDate));
 
    char* serial[9];
    usbGetSerialNumber_USB1608G(udev, (char*)serial);
    printf("\tSerial number = %s\n", (char*)serial);
    uint16_t version = 0;
    usbFPGAVersion_USB1608G(udev, &version);
    printf("\tFPGA version %02x.%02x\n", version >> 0x8, version & 0xff);

  }
  
  
  return pyudev;
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Device deactivation
int deactivate_device(pyudev_t pyudev, _Bool quiet) {

  // Unpack pyudev struct contents
  libusb_device_handle *udev = PyCapsule_GetPointer(pyudev.udev_capsule, "udev");
  usbAInScanStop_USB1608G(udev);
  usbAInScanClearFIFO_USB1608G(udev);
  usbDLatchW_USB1608G(udev, 0x0);                  // zero out the DIO
  if (pyudev.usb1608GX_2AO) {
	  usbAOutScanStop_USB1608GX_2AO(udev);
	  usbAOut_USB1608GX_2AO(udev, 0, 0x0, pyudev.table_AO);
	  usbAOut_USB1608GX_2AO(udev, 1, 0x0, pyudev.table_AO);
  }
  cleanup_USB1608G(udev);
  
  // deallocate memory for analog input buffer.
  if (pyudev.buffer != NULL) {
      free(pyudev.buffer);
  }

  return 1;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Set differential or single ended mode and gains on analog channels
pyudev_t set_analog_config(pyudev_t pyudev, _Bool differential, uint8_t gains[], int n_samples, _Bool quiet) {

    uint8_t mode, gain, channel;
    
    // Unpack pyudev struct contents
    libusb_device_handle *udev = PyCapsule_GetPointer(pyudev.udev_capsule, "udev");
    
    if (differential) {
        mode = SINGLE_ENDED;
        pyudev.n_channels = 8;
    } else {
        mode = DIFFERENTIAL;
        pyudev.n_channels = 16;
    }
    
    for (channel = 0; channel < pyudev.n_channels; channel++) {
	  switch(gains[channel]) {
	    case 10: gain = BP_10V; break;
	    case 5: gain = BP_5V; break;
	    case 2: gain = BP_2V; break;
	    case 1: gain = BP_1V; break;
	    default:  gain = BP_10V; break;
	  }
	  pyudev.list[channel].range = gain;  
	  pyudev.list[channel].mode = mode;
	  pyudev.list[channel].channel = channel;
	}   
    
    pyudev.list[pyudev.n_channels-1].mode |= LAST_CHANNEL;

    // Record settings for persistence
    pyudev.n_samples = n_samples;

    // Setup
    usbAInConfig_USB1608G(udev, pyudev.list);
    //usbAInScanStop_USB1608G(udev);
	//usbAInScanClearFIFO_USB1608G(udev);

    // Allocate memory for analog input buffer.
    if (pyudev.buffer != NULL) {
        free(pyudev.buffer); // Free old memory as n_samples may have changed.
    }
    pyudev.buffer = malloc(2*pyudev.n_channels*pyudev.n_samples);
    if (pyudev.buffer == NULL) {
      perror("Can not allocate memory for buffer");
    }

    // Debugging
    /*for (channel = 0; channel < pyudev.n_channels; channel++) {
        printf("\tCh. %d Range=%d, Mode=%d\n",pyudev.list[channel].channel, pyudev.list[channel].range,pyudev.list[channel].mode);
    }*/
    
    return pyudev;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Read analog channels into preallocated buffer, then compute calibrated voltages and store this as an array.
// A pointer to the array (volts) is passed in which could be a NumPy array ready to be filled.
int analog_read(pyudev_t pyudev, double sample_rate, _Bool quiet, double* volts) {
    
    // Unpack pyudev struct contents
    libusb_device_handle *udev = PyCapsule_GetPointer(pyudev.udev_capsule, "udev");
    
    if (pyudev.buffer == NULL) {
      perror("No memory for buffer");
      return 0;
    }

    if (volts == NULL) {
      perror("No memory for output volts");
      return 0;
    }

    //if (!quiet) printf("\tn_ch = %i, n_samples = %i\n", pyudev.n_channels, pyudev.n_samples);

    // Setup
    //usbAInConfig_USB1608G(udev, pyudev.list);
    usbAInScanStop_USB1608G(udev);
    usbAInScanClearFIFO_USB1608G(udev);
    
    // Acquire    - here could specify triggering with last byte (mode) but currently set to free-run
    usbAInScanStart_USB1608G(udev, pyudev.n_samples, 0, sample_rate, 0x0);
    int ret = usbAInScanRead_USB1608G(udev, pyudev.n_samples, pyudev.n_channels, pyudev.buffer);
    if (!quiet) printf("\nn bytes read = %i, should be %i\n", ret, 2*pyudev.n_channels*pyudev.n_samples);

    usbAInScanStop_USB1608G(udev);
    usbAInScanClearFIFO_USB1608G(udev);

    // Post process to voltage
    int i,j,k;
    uint8_t gain;
    uint16_t s;
    for (i = 0; i < pyudev.n_samples; i++) {
        //printf("In C: %6d", i);
        for (j = 0; j < pyudev.n_channels; j++) {
              gain = pyudev.list[j].range;
              k = i*pyudev.n_channels + j;
              s = rint(pyudev.buffer[k]*pyudev.table_AIN[gain][0] + pyudev.table_AIN[gain][1]);
              volts[k] = volts_USB1608G(gain, s);
              //printf(", %8.4lf", volts[k]); //volts_USB1608G(gain, s));
        }
        //printf("\n");
      }
   
    return 1;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Assign digital pins
int set_digital_direction(pyudev_t pyudev, _Bool inputMode, _Bool quiet) {

    // Unpack pyudev struct contents
    libusb_device_handle *udev = PyCapsule_GetPointer(pyudev.udev_capsule, "udev");

    // Set the mode ...
    usbDTristateW_USB1608G(udev,0xf0);
    
    return 1;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Read digital pins
uint8_t digital_read(pyudev_t pyudev) {

    // Unpack pyudev struct contents
    libusb_device_handle *udev = PyCapsule_GetPointer(pyudev.udev_capsule, "udev");

    // Read the digital pin states

    return usbDLatchR_USB1608G(udev);;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Read counter
uint16_t counter_read(pyudev_t pyudev, int counter) {
    // Unpack pyudev struct contents
    libusb_device_handle *udev = PyCapsule_GetPointer(pyudev.udev_capsule, "udev");
 
    int c;
    if (counter==0) c=COUNTER0;
    if (counter==1) c=COUNTER1;
    return usbCounter_USB1608G(udev, c);
}
