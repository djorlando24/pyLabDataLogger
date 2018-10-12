/*
  Analog-to-serial firmware 
  compatible with pyLabDataLogger

  For Leonardo 5V Beetle board inside PMDI controller.
  Differential ADC reading of A1-A0.
  Currently wired up to read the 5V signal from the
  water circuit pressure transducer inside the 
  heater unit.
  
  Calibration data for PT001 generic 100psi automotive
  sensor, as of 14/3/18 has been entered.
  
  Daniel Duke
  13 Oct 2018
*/

int n=0;
#define COUNTS_PER_VOLT 204.8
#define PSI_PER_VOLT 24.496
#define PSI_OFFSET -13.427
#define UNIT "psig"
#define DESCRIPTOR "Heater Water Pressure"
#define VARNAME "Pwater"

// the setup routine runs once when you press reset:
void setup() {
  pinMode(A0,INPUT);
  pinMode(A1,INPUT);
  pinMode(A2,INPUT);
  pinMode(13,OUTPUT); //led
  
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
}

// the loop routine runs over and over again forever:
void loop() {
  int groundValue = analogRead(A0);
  int sensorValue = analogRead(A1);

  //reference
  sensorValue -= groundValue;

  //floating point calcs
  float scaledOutput = (float)sensorValue/COUNTS_PER_VOLT;
  scaledOutput *= PSI_PER_VOLT;
  scaledOutput += PSI_OFFSET;

  //serial print
  Serial.print(DESCRIPTOR);
  Serial.print(": ");
  Serial.print(VARNAME);
  Serial.print("=");
  Serial.print(scaledOutput);
  Serial.print(" ");
  Serial.print(UNIT);
  Serial.print(", RawADCValue=");
  Serial.print(sensorValue);
  Serial.println(" /1024cts");

  //blink
  n++;
  if (n>=20) {
     digitalWrite(13,HIGH);
     n=0;
  } else digitalWrite(13,LOW);

  delay(100);        // delay in between reads for stability
}
