/*
 *
 *  Copyright (c) 2015 Warren J. Jasper <wjasper@tx.ncsu.edu>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
*/

#ifndef USB_7202_H

#define USB_7202_H
#ifdef __cplusplus
extern "C" { 
#endif

#include <stdint.h>

#define USB7202_PID     (0x00f2)

/* Commands and USB Report ID for USB-7202 */

/* MBD Control Transfers */
#define STRING_MESSAGE  (0x80)  // Send string messages to the device
#define RAW_DATA        (0x81)  // Return RAW data from the device

/* UL Control TRansfers */
    // Digital I/O Commands
#define DCONFIG_PORT    (0x0)   // Configure digital port
#define DCONFIG_BIT     (0x1)   // Configure individual port bits
#define DPORT           (0x2)   // Read/Write digital port
#define DPORT_BIT       (0x3)   // Read/Write port bit
    // Analog Input Commands
#define AIN             (0x10)  // Read analog input channel
#define AIN_SCAN        (0x11)  // Scan analog input channels
#define AIN_STOP        (0x12)  // Stop ananlog input scan
#define ALOAD_QUEUE     (0x13)  // Load the channel/gain queue
    // Counter Commands
#define COUNTER         (0x20)  // Read/initialize counter
    // Memory Commands
#define MEMORY          (0x30)  // Read/Write memory
#define MEMORY_ADDR     (0x31)  // Read/Write memory address
    // Miscellaneous Commands
#define BLINK_LED       (0x40)  // Cause LED to blink
#define RESET           (0x41)  // Force a device reset
#define TRIGGER_CONFIG  (0x42)  // Configure external trigger
#define SYNC_CONFIG     (0x43)  // Configure sync input/output
#define STATUS          (0x44)  // Retrieve device status
#define CAL_CONFIG      (0x45)  // Control CAL MUX
#define SERIAL          (0x48)  // Read/Write serial number
      // Code Update Commands
#define UPDATE_MODE     (0x50)  // Put device into code update mode
#define UPDATE_ADDR     (0x51)  // Set code download address
#define UPDATE_DATA     (0x52)  // Download code image
#define UPDATE_CHECKSUM (0x53)  // Read/download checksum
#define UPDATE_FLASH    (0x54)  // Write image to program memory and reset
#define READ_CODE       (0x55)  // Read FLASH program memory

#define EXT_TRIG_FAILING_EDGE 0;
#define EXT_TRIG_RAISING_EDGE 1;
#define SYNC_MASTER 0
#define SYNC_SLAVE  1

#define NCHAN_USB7202     8  // max number of ADC channels
#define NGAINS_USB7202    8  // max number of gain levels

#define DIO_DIR_IN  (0x01)
#define DIO_DIR_OUT (0x00)

// Gain Ranges
#define BP_10_00V  (0x0)           // Single Ended +/- 10.0 V
#define BP_5_00V   (0x1)           // Single Ended +/- 5.00 V
#define BP_2_50V   (0x2)           // Single Ended +/- 2.50 V
#define BP_2_00V   (0x3)           // Single Ended +/- 2.00 V
#define BP_1_25V   (0x4)           // Single Ended +/- 1.25 V
#define BP_1_00V   (0x5)           // Single Ended +/- 1.00 V
#define BP_0_625V  (0x6)           // Single Ended +/- 0.625 V
#define BP_0_3125V (0x7)           // Single Ended +/- 0.3125 V

typedef struct Calibration_AIN_t {
  float slope;
  float intercept;
} Calibration_AIN;

// options for AInScan
#define AIN_EXECUTION     0x1  // 1 = single execution, 0 = continuous execution
#define AIN_BURST_MODE    0x2  // 1 = burst I/O mode,   0 = normal I/O mode
#define AIN_TRANSFER_MODE 0x4  // 1 = Immediate Transfer mode  0 = block transfer mode
#define AIN_TRIGGER       0x8  // 1 = Use External Trigger
#define AIN_EXTERN_SYNC   0x10 // 1 = Use External Sync
#define AIN_DEBUG_MODE    0x20 // 1 = debug mode

/* Status bit values */
#define AIN_SCAN_OVERRUN   (0x1 << 2)

/* function prototypes for the USB-7202 */
void usbDConfigPortR_USB7202(libusb_device_handle *udev, uint8_t *direction);
void usbDConfigPort_USB7202(libusb_device_handle *udev, uint8_t direction);
void usbDConfigBitR_USB7202(libusb_device_handle *udev, uint8_t bitnum, uint8_t *direction);
void usbDConfigBit_USB7202(libusb_device_handle *udev, uint8_t bitnum, uint8_t direction);
uint8_t usbDPortR_USB7202(libusb_device_handle *udev);
void usbDPortW_USB7202(libusb_device_handle *udev, uint8_t value);
uint16_t usbAIn_USB7202(libusb_device_handle *udev, uint8_t channel, uint8_t range);
void usbAInScan_USB7202(libusb_device_handle *udev, uint8_t lowchannel, uint8_t highchannel, uint32_t count, double *frequency, uint8_t options);
int usbAInScanRead_USB7202(libusb_device_handle *udev, int nScan, int nChan, uint16_t *data);
void usbAInStop_USB7202(libusb_device_handle *udev);
void usbAInLoadQueue_USB7202(libusb_device_handle *udev, uint8_t gainArray[NCHAN_USB7202]);
void usbInitCounter_USB7202(libusb_device_handle *udev);
uint32_t usbReadCounter_USB7202(libusb_device_handle *udev);
void usbReadMemory_USB7202(libusb_device_handle *udev, uint8_t count, uint8_t* data);
void usbWriteMemory_USB7202(libusb_device_handle *udev, uint8_t count, uint8_t* data);
uint16_t usbReadMemoryAddress_USB7202(libusb_device_handle *udev);
void usbWriteMemoryAddress_USB7202(libusb_device_handle *udev, uint16_t address);
void usbBlinkLED_USB7202(libusb_device_handle *udev, uint8_t count);
void usbReset_USB7202(libusb_device_handle *udev, uint8_t type);
void usbTriggerConfig_USB7202(libusb_device_handle *udev, uint8_t type);
void usbSyncConfig_USB7202(libusb_device_handle *udev, uint8_t type);
uint16_t usbStatus_USB7202(libusb_device_handle *udev);
void usbCalConfig_USB7202(libusb_device_handle *udev, uint8_t setting);
void usbGetSerialNumber_USB7202(libusb_device_handle *udev, char serial[9]);
void usbSetSerialNumber_USB7202(libusb_device_handle *udev, char serial[9]);
void usbUpdateMode_USB7202(libusb_device_handle *udev);
void usbUpdateAddress_USB7202(libusb_device_handle *udev, uint8_t address[3]);
void usbUpdateData_USB7202(libusb_device_handle *udev, uint8_t count, uint8_t *data);
void usbUpdateChecksum_USB7202(libusb_device_handle *udev, uint16_t *checksum);
void usbUpdateFlash_USB7202(libusb_device_handle *udev);
void usbReadCode_USB7202(libusb_device_handle *udev, uint8_t address[3], uint8_t count, uint8_t *data);
void usbBuildGainTable_USB7202(libusb_device_handle *udev, Calibration_AIN table[NGAINS_USB7202][NCHAN_USB7202]);
double volts_USB7202(uint16_t value, uint8_t range);
void getMFGCAL_USB7202(libusb_device_handle *udev, struct tm *date);

#ifdef __cplusplus
} /* closing brace for extern "C" */
#endif
#endif // USB_7202_H
