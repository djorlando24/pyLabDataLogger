//  Water pump monitor firmware
//  v1.0
//
//  Daniel Duke
//  < daniel.duke@monash.edu >
//
//  Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
//  Department of Mechanical & Aerospace Engineering
//  Monash University, Australia
//
//  Intended hardware = Teensy 3.2
//  
//  This software will record several sensor values and export them to USB Serial for
//  data logging. Serial1 is connected to a MAX485 chip which talks to an Omega iSeries
//  Process Controller. We expect the iSeries to be transmitting in RS-485 at 600 baud
//  with 7 data bits, 1 stop bit, odd parity. Units transmission should be turned on and
//  device should be in command (not continuous) mode.
//  
//  The code also counts pulses for a flowmeter, records analog voltage from a pressure
//  transducer connected via a voltage divider, and reports on the status of several
//  relays.

// Last Update 13/2/2020

#include <FreqMeasure.h>

// Hardware setup
#define FLOW_PULSE_PIN 3 // This cannot be changed
#define INT_LED 13       // This cannot be changed
#define EXT_LED 5
#define EXT_LED_GND 4
#define PRESSURE_INPUT A0
#define RELAY_SRC0 19
#define WATER_LEVEL_RELAY 20
#define RELAY_SRC1 16
#define HEAT_ON_RELAY 17
#define ISERIES_SER Serial3
#define ISERIES_RE 6 //RS-485 Read Enable (does nothing for RS-232)
#define ISERIES_DE 9 //RS-485 Drive Enable (does nothing for RS-232)
#define PUMP_CUTOUT 23

#define ISERIES_BAUD 9600
#define ISERIES_MODE SERIAL_8N1
#define ISERIES_TIMEOUT 1000 // milliseconds
#define ISERIES_RC 0x2A // recognition character - default to asterisk
#define USBSERIAL_BAUD 9600


// Software setup
#define HEADER_STRING "pMDI Rig Water Heater"
#define PRESSURE_UNIT "psig"
#define PRESSURE_SCALE 0.0966796875 // convert 2.5V=1024c via voltage divider into 150psi
#define PRESSURE_OFFSET -14.5 // psig
#define FLOWRATE_UNIT "Hz"
#define FLOWMETER_SCALE 1.0
#define FLOWMETER_OFFSET 0.0
#define LOOP_DELAY 2000 // min time between refreshing

// Set up global variables
#define ISERIES_BUFLEN 64
char pctrl_set1[ISERIES_BUFLEN];
char pctrl_set2[ISERIES_BUFLEN];
char pctrl_curr[ISERIES_BUFLEN];
char pctrl_peak[ISERIES_BUFLEN];
char pctrl_valy[ISERIES_BUFLEN];
char pctrl_alrm[ISERIES_BUFLEN];
char buf[ISERIES_BUFLEN];
char internalbuf[ISERIES_BUFLEN];
int n;
const char noResult[ISERIES_BUFLEN] = "None";

// Set up pins
void setup() {
  // GPIOs
  pinMode(INT_LED, OUTPUT);
  pinMode(EXT_LED, OUTPUT);
  pinMode(EXT_LED_GND, OUTPUT);
  digitalWrite(EXT_LED_GND, LOW);
  pinMode(ISERIES_DE, OUTPUT);
  pinMode(ISERIES_RE, OUTPUT);
  digitalWrite(ISERIES_DE, LOW);
  digitalWrite(ISERIES_RE, LOW);
  pinMode(RELAY_SRC0, OUTPUT);
  digitalWrite(RELAY_SRC0, LOW);
  pinMode(RELAY_SRC1, OUTPUT);
  digitalWrite(RELAY_SRC0, LOW);
  pinMode(WATER_LEVEL_RELAY, INPUT_PULLUP);
  pinMode(HEAT_ON_RELAY, INPUT_PULLUP);
  pinMode(PUMP_CUTOUT, INPUT);
  digitalWrite(PUMP_CUTOUT, LOW); // try to pull it low if floating

  // Frequency counter
  pinMode(FLOW_PULSE_PIN, INPUT);
  FreqMeasure.begin();
  
  // Analog inputs
  pinMode(PRESSURE_INPUT, INPUT);

  // Serial ports
  Serial.begin(USBSERIAL_BAUD); // USB Serial
  ISERIES_SER.begin(ISERIES_BAUD, ISERIES_MODE); // Hardware serial for RS-485 to Omega iSeries

  // Attempt communication with Omega iSeries on startup
  //if ((Serial.available() > 0) && (ISERIES_SER.available() > 0)) {
  /*
  if (1==1) {
    fISERIEScomm("*\x01R\x05\r",buf);
    Serial.print(HEADER_STRING);
    Serial.print("/ISERIES/ID = ");
    Serial.println(buf);
  }
  */
}

// MAIN LOOP /////////////////////////////////////////////////////////////////////////////////////////
void loop() {
  if (Serial) {
    
    Serial.print(HEADER_STRING);
    Serial.print("/Water Pressure = ");
    sprintf(buf,"%f %s\n",fread_pressure(),PRESSURE_UNIT);
    Serial.print(buf);

    Serial.print(HEADER_STRING);
    Serial.print("/Flow Rate = ");
    sprintf(buf,"%f %s\n",fread_flowrate(),FLOWRATE_UNIT);
    Serial.print(buf);
    
    Serial.print(HEADER_STRING);
    sprintf(buf,"/Low water alarm = %i\n", digitalRead(WATER_LEVEL_RELAY));
    Serial.print(buf);
    
    Serial.print(HEADER_STRING);
    sprintf(buf,"/ISERIES/Heater power duty = %i\n", digitalRead(HEAT_ON_RELAY));
    Serial.print(buf);
    
    Serial.print(HEADER_STRING);
    sprintf(buf,"/Pump cutout override = %i\n", digitalRead(PUMP_CUTOUT));
    Serial.print(buf);
    
    fread_process_controller();

    led_heartbeat();
    
  } else {

    // flash an error code indicating failure to use Serial
    for (n=0;n<3;n++) {
      led_heartbeat();
      delay(200);
    }
    
  }

  // Min. time between updates on Serial
  delay(LOOP_DELAY);
  Serial.print("\r\n");
  Serial.flush();
}
/////////////////////////////////////////////////////////////////////////////////////////////////////

double fread_pressure() {
  return float(analogRead(PRESSURE_INPUT))*PRESSURE_SCALE + PRESSURE_OFFSET;
}

double fread_flowrate() {
  if (FreqMeasure.available()) {
    return float(FreqMeasure.countToFrequency(FreqMeasure.read()))*FLOWMETER_SCALE + FLOWMETER_OFFSET;
  } else {
    return -1.0;
  }
}

void led_heartbeat() {
  digitalWrite(EXT_LED,HIGH);
  delay(250);
  digitalWrite(EXT_LED,LOW);
  return;
}

// remove newlines from char arrays
void fstrip_newlines(char* p) {
    char* q = p;
    while (p != 0 && *p != '\0') {
        if (*p == '\n') {
            p++;
            *q = *p;
        } 
        else {
            *q++ = *p++;
        }
    }
    *q = '\0';
    return;
}


// Function to transmit cmd_str and buffer the reply into s
void fISERIEScomm(char* cmd_str, char* s, int expected_len=6, bool verbose=0) {

  // Transmit 
  digitalWrite(ISERIES_DE, HIGH);
  digitalWrite(ISERIES_RE, LOW);
  delay(1);
  ISERIES_SER.print(cmd_str);
  if (verbose) Serial.println(cmd_str);
  ISERIES_SER.flush();
  if (verbose) Serial.flush();
  delay(1);
  digitalWrite(ISERIES_DE, LOW);
  digitalWrite(ISERIES_RE, HIGH);

  long t0 = millis();
  int n=0;
  while (((millis() - t0) < ISERIES_TIMEOUT) && (n<expected_len)) {
    if (ISERIES_SER.available() > 0) {
      n = ISERIES_SER.readBytes(s,ISERIES_BUFLEN);
      if (verbose) {
         Serial.print(n);
         Serial.print(" bytes received: ");
         Serial.println(s);
      }
    } else {
      delay(1);
    }
  }

  fstrip_newlines(s);
  
  digitalWrite(ISERIES_DE, LOW);
  digitalWrite(ISERIES_RE, LOW);
  if (verbose) Serial.println();
  
  return;
}

// Decode strings from ISERIES
void fISERIESdecodesetpoint(char* in, char* out) {
  if (sizeof(in)<3) {
    strcpy((char*)noResult,out);
  } else {
    char sign=' ';
    if ((in[0] & 0b1000) == 1) sign='-';
    float multiplier=1.0;
    switch (in[0] & 0b0111) {
      case 2: multiplier=0.1; break;
      case 3: multiplier=0.01; break;
      case 4: multiplier=0.001; break;
    }
    sprintf(out,"%.1f",strtol(in+3,0,16)*multiplier);
  }
  return;
}

void fISERIESdecodealarm(char* in, char* out) {
  if (sizeof(in)<1) {
    strcpy((char*)noResult,out);
  } else {
    //Serial.print('<');
    //Serial.print(in[0]);
    //Serial.println('>');
    switch (in[0]) {
      case '@': sprintf(out,"0"); break;
      case 'A': sprintf(out,"1"); break;
      case 'B': sprintf(out,"2"); break;
      case 'C': sprintf(out,"12"); break;
      default: sprintf(out,"NaN");
    }
  }
  return;
}

// Communicate with Omega iSeries process controller
// to obtain certain variables we want.
void fread_process_controller() {
  
  // Read set point, current value and alarms
  if (ISERIES_SER==1) {

    char cmd[ISERIES_BUFLEN];
    char ppb[ISERIES_BUFLEN];
    sprintf(cmd,"%cR01\r",ISERIES_RC); // set pt 1
    fISERIEScomm(cmd,ppb,6);
    fISERIESdecodesetpoint(ppb,pctrl_set1);
    
    sprintf(cmd,"%cR02\r",ISERIES_RC); // set pt 2
    fISERIEScomm(cmd,ppb,6);
    fISERIESdecodesetpoint(ppb,pctrl_set2);
    
    sprintf(cmd,"%cX01\r",ISERIES_RC,5); // current value
    fISERIEScomm(cmd,pctrl_curr);
    
    sprintf(cmd,"%cX02\r",ISERIES_RC,5); // peak value
    fISERIEScomm(cmd,pctrl_peak);
    
    sprintf(cmd,"%cX03\r",ISERIES_RC,5); // valley value
    fISERIEScomm(cmd,pctrl_valy);
    
    sprintf(cmd,"%cU01\r",ISERIES_RC,1); // alarms status
    fISERIEScomm(cmd,ppb);
    fISERIESdecodealarm(ppb,pctrl_alrm);
    
  } else {
    
    strcpy((char*)noResult,pctrl_set1);
    strcpy((char*)noResult,pctrl_set2);
    strcpy((char*)noResult,pctrl_curr);
    strcpy((char*)noResult,pctrl_peak);
    strcpy((char*)noResult,pctrl_valy);
    strcpy((char*)noResult,pctrl_alrm);

    // flash an error code indicating failure to use ISERIES_SER
    for (n=0;n<2;n++) {
      led_heartbeat();
      delay(200);
    }
    
  }
  
  // Report values to Serial
  sprintf(buf,"\n%s/ISERIES/Temp Set Point 1 = %s\n",HEADER_STRING,pctrl_set1);
  Serial.print(buf);
  sprintf(buf,"%s/ISERIES/Temp Set Point 2 = %s\n",HEADER_STRING,pctrl_set2);
  Serial.print(buf);
  sprintf(buf,"%s/ISERIES/Current Temp = %s\n",HEADER_STRING,pctrl_curr);
  Serial.print(buf);
  sprintf(buf,"%s/ISERIES/Peak Temp = %s\n",HEADER_STRING,pctrl_peak);
  Serial.print(buf);
  sprintf(buf,"%s/ISERIES/Valley Temp = %s\n",HEADER_STRING,pctrl_valy);
  Serial.print(buf);
  sprintf(buf,"%s/ISERIES/Alarm State = %s\n",HEADER_STRING,pctrl_alrm);
  Serial.print(buf);
  

  return;
}
