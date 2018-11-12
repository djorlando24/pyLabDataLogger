/*
 *
 *  Copyright (c) 2014 Warren J. Jasper <wjasper@tx.ncsu.edu>
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


#ifndef USB_CTR_H

#define USB_CTR_H
#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

#define USB_CTR08_PID      (0x0127)
#define USB_CTR04_PID      (0x012E)

#define NTIMER    4        // Number of PWM Timers
#define NCOUNTER  8        // Number of Counters
  

 /* Commands and HID Report ID for USB-CTR  */
 /* Digital I/O Commands */
#define DTRISTATE            (0x00)  // Read/Write Tristate register
#define DPORT                (0x01)  // Read digital port pins
#define DLATCH               (0x02)  // Read/Write Digital port output latch register
  
/* Counter Commands */
#define COUNTER              (0x10)  // Read or set the counter's value
#define COUNTER_MODE         (0x11)  // Read or set the counter's mode
#define COUNTER_OPTIONS      (0x12)  // Read or set the counter's options
#define COUNTER_DEBOUNCE     (0x13)  // Read or set the counter's debounce options
#define COUNTER_GATE_CONFIG  (0x14)  // Read or set the options for the Counter Gate
#define COUNTER_OUT_CONFIG   (0x15)  // Read or set the options for the Counter Out
#define COUNTER_OUT_VALUES   (0x16)  // Read or set the counter's output values
#define COUNTER_LIMIT_VALUES (0x17)  // Read or set the limit values
#define COUNTER_PARAMETERS   (0x18)  // Read or set all of one counter's parameters
  
/* Acquisition Comands */
#define SCAN_CONFIG          (0x20)  // Read/Write the scan list
#define SCAN_START           (0x21)  // Start input scan
#define SCAN_STOP            (0x22)  // Stop input scan
#define SCAN_CLEAR_FIFO      (0x23)  // Clear data in the input FIFO
#define BULK_FLUSH           (0x24)  // Flush the Bulk pipe

/* Timer Commands */
#define TIMER_CONTROL        (0x28)  // Read/Write timer control register
#define TIMER_PERIOD         (0x29)  // Read/Write timer period register
#define TIMER_PULSE_WIDTH    (0x2A)  // Read/Write timer pulse width registers
#define TIMER_COUNT          (0x2B)  // Read/Write timer count registers
#define TIMER_START_DELAY    (0x2C)  // Read/Write timer start delay registers
#define TIMER_PARAMETERS     (0x2D)  // Read/Write all timer parameters at once

/* Memory Commands */
#define MEMORY               (0x30)  // Read/Write EEPROM
#define MEM_ADDRESS          (0x31)  // EEPROM read/write address value
#define MEM_WRITE_ENABLE     (0x32)  // Enable writes to firmware area

/* Miscellaneous Commands */
#define STATUS               (0x40)  // Read device status
#define BLINK_LED            (0x41)  // Causes the LED to blink
#define RESET                (0x42)  // Reset the device
#define TRIGGER_CONFIG       (0x43)  // External trigger configuration
#define SERIAL               (0x48)  // Read/Write USB Serial Number

/* FPGA Configuration Commands */
#define FPGA_CONFIG          (0x50) // Start FPGA configuration
#define FPGA_DATA            (0x51) // Write FPGA configuration data
#define FPGA_VERSION         (0x52) // Read FPGA version

  /* Status bit values */
#define PACER_RUNNING      (0x1 << 1)
#define SCAN_OVERRUN       (0x1 << 2)
#define SCAN_DONE          (0x1 << 5)
#define FPGA_CONFIGURED    (0x1 << 8)
#define FPGA_CONFIG_MODE   (0x1 << 9)

// Mode Register
#define TOTALIZE            (0x0)
#define PERIOD              (0x1)
#define PULSEWIDTH          (0x2)
#define TIMING              (0x3)
#define PERIOD_MODE_1X      (0x0)
#define PERIOD_MODE_10X     (0x1 << 2)
#define PERIOD_MODE_100X    (0x2 << 2)
#define PERIOD_MODE_1000X   (0x3 << 2)
#define TICK_SIZE_20_83ns   (0x0)
#define TICK_SIZE_208_3ns   (0x1 << 4)
#define TICK_SIZE_2083_3ns  (0x2 << 4)
#define TICK_SIZE_20833_3ns (0x3 << 4)  

// Options Register
#define CLEAR_ON_READ (0x1 << 0)
#define NO_RECYCLE    (0x1 << 1)
#define COUNT_DOWN    (0x1 << 2)
#define RANGE_LIMIT   (0x1 << 3)
#define FALLING_EDGE  (0x1 << 4)

typedef struct counterParams_t {
  uint8_t counter;
  uint8_t modeOptions;
  uint8_t counterOptions;
  uint8_t gateOptions;
  uint8_t outputOptions;
  uint8_t debounce;
} CounterParams;  

typedef struct timerParams_t {
  uint8_t timer;
  uint32_t period;
  uint32_t pulseWidth;
  uint32_t count;
  uint32_t delay;
} TimerParams;

typedef struct scanList_t {
  uint8_t lastElement;    // the last element of the scan list
  uint8_t scanList[33];   // the channel configuration
} ScanList;


/* function prototypes for the USB-CTR */
void usbInit_CTR(libusb_device_handle *udev);
void usbDTristateW_USB_CTR(libusb_device_handle *udev, uint16_t value);
uint16_t usbDTristateR_USB_CTR(libusb_device_handle *udev);
uint16_t usbDPort_USB_CTR(libusb_device_handle *udev);
void usbDLatchW_USB_CTR(libusb_device_handle *udev, uint16_t value);
uint16_t usbDLatchR_USB_CTR(libusb_device_handle *udev);
void usbBlink_USB_CTR(libusb_device_handle *udev, uint8_t count);
void cleanup_USB_CTR( libusb_device_handle *udev);
void usbGetSerialNumber_USB_CTR(libusb_device_handle *udev, char serial[9]);
void usbReset_USB_CTR(libusb_device_handle *udev);
void usbFPGAConfig_USB_CTR(libusb_device_handle *udev);
void usbFPGAData_USB_CTR(libusb_device_handle *udev, uint8_t *data, uint8_t length);
void usbFPGAVersion_USB_CTR(libusb_device_handle *udev, uint16_t *version);
uint16_t usbStatus_USB_CTR(libusb_device_handle *udev);
void usbMemoryR_USB_CTR(libusb_device_handle *udev, uint8_t *data, uint16_t length);
void usbMemoryW_USB_CTR(libusb_device_handle *udev, uint8_t *data, uint16_t length);
void usbMemAddressR_USB_CTR(libusb_device_handle *udev, uint16_t address);
void usbMemAddressW_USB_CTR(libusb_device_handle *udev, uint16_t address);
void usbMemWriteEnable_USB_CTR(libusb_device_handle *udev);
void usbTriggerConfig_USB_CTR(libusb_device_handle *udev, uint8_t options);
void usbTriggerConfigR_USB_CTR(libusb_device_handle *udev, uint8_t *options);
void usbTimerControlR_USB_CTR(libusb_device_handle *udev, uint8_t timer, uint8_t *control);
void usbTimerControlW_USB_CTR(libusb_device_handle *udev, uint8_t timer, uint8_t control);
void usbTimerPeriodR_USB_CTR(libusb_device_handle *udev, uint8_t timer, uint32_t *period);
void usbTimerPeriodW_USB_CTR(libusb_device_handle *udev, uint8_t timer, uint32_t period);
void usbTimerPulseWidthR_USB_CTR(libusb_device_handle *udev, uint8_t timer, uint32_t *pulseWidth);
void usbTimerPulseWidthW_USB_CTR(libusb_device_handle *udev, uint8_t timer,uint32_t pulseWidth);
void usbTimerCountR_USB_CTR(libusb_device_handle *udev, uint8_t timer, uint32_t *count);
void usbTimerCountW_USB_CTR(libusb_device_handle *udev, uint8_t timer, uint32_t count);
void usbTimerDelayR_USB_CTR(libusb_device_handle *udev, uint8_t timer, uint32_t *delay);
void usbTimerDelayW_USB_CTR(libusb_device_handle *udev, uint8_t timer, uint32_t delay);
void usbTimerParamsR_USB_CTR(libusb_device_handle *udev, uint8_t timer, TimerParams *params);
void usbTimerParamsW_USB_CTR(libusb_device_handle *udev, uint8_t timer, TimerParams params);
void usbCounterSet_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint64_t count);
uint64_t usbCounter_USB_CTR(libusb_device_handle *udev, uint8_t counter);  
void usbCounterModeR_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t *mode);
void usbCounterModeW_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t mode);
void usbCounterOptionsR_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t *options);
void usbCounterOptionsW_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t options);
void usbCounterDebounceR_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t *debounce);
void usbCounterDebounceW_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t debounce);
void usbCounterGateConfigR_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t *options);
void usbCounterGateConfigW_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t options);
void usbCounterOutConfigR_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t *options);
void usbCounterOutConfigW_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t options);
void usbCounterOutValuesR_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t index, uint64_t *value);
void usbCounterOutValuesW_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t index, uint64_t value);
void usbCounterLimitValuesR_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t index, uint64_t *value);
void usbCounterLimitValuesW_USB_CTR(libusb_device_handle *udev, uint8_t counter, uint8_t index, uint64_t value);
void usbCounterParamsR_USB_CTR(libusb_device_handle *udev, uint8_t counter, CounterParams *params);
void usbCounterParamsW_USB_CTR(libusb_device_handle *udev, uint8_t counter, CounterParams params);

void usbScanConfigR_USB_CTR(libusb_device_handle *udev, uint8_t lastElement, ScanList *scanList);
void usbScanConfigW_USB_CTR(libusb_device_handle *udev, uint8_t lastElement, ScanList scanList);
void usbScanStart_USB_CTR(libusb_device_handle *udev, uint32_t count, uint32_t retrig_count, uint32_t pacer_period, uint8_t options);
void usbScanStop_USB_CTR(libusb_device_handle *udev);
void usbScanClearFIFO_USB_CTR(libusb_device_handle *udev);
void usbScanBulkFlush_USB_CTR(libusb_device_handle *udev, uint8_t count);
int usbScanRead_USB_CTR(libusb_device_handle *udev, int count, int lastElement, uint16_t *data);

#ifdef __cplusplus
} /* closing brace for extern "C" */
#endif
#endif //USB_CTR

