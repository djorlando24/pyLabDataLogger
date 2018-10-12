/* usbtc08.i - SWIG interface file for Pico Technology TC-08 driver */

/* Include other SWIG interface files */
%include "stdint.i"
%include "typemaps.i"
%include "carrays.i"

%module usbtc08
%{
/* Build resulting C file as Python extension */
#define SWIG_FILE_WITH_INIT
/* Header file of libusbtc08 library */
#include "/opt/picoscope/include/libusbtc08-1.8/usbtc08.h"
%}

%typemap(out) int8_t[ANY] {
  int i;
  PyObject *list = PyList_New($1_dim0);
  for (i = 0; i < $1_dim0; ++i) {
    PyList_SetItem(list, i, PyInt_FromLong($1[i]));
  }
  $result = list;
}

%array_class(float, floatArray);
%array_class(int, intArray);
%array_class(short, shortArray);
%array_class(signed char, charArray);

int16_t usb_tc08_open_unit_progress(
  int16_t *OUTPUT,  /* *handle */
  int16_t *OUTPUT); /* *percent_progress */

int16_t usb_tc08_get_unit_info(
  int16_t handle,
  USBTC08_INFO *OUTPUT); /* *info */

%include "/opt/picoscope/include/libusbtc08-1.8/usbtc08.h"

%constant int sizeof_USBTC08_INFO = sizeof(USBTC08_INFO);
