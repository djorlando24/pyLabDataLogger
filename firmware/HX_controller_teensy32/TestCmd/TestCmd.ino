// Sweep possible recognition characters to speak with iSeries.

// set this to the hardware serial port you wish to use
#define HWSERIAL Serial3

void setup() {
	Serial.begin(9600);
	HWSERIAL.begin(9600,SERIAL_8N1);
}

char CMD[8];
char rc = 0x20;

void loop() {

  
        int incomingByte;
        char buf[64];
        int i=0;
        
        
    sprintf(CMD,"%cR01\r",rc); // *Z02
    rc ++;
    if (rc > 0x7F) rc = 0x20;
	
		HWSERIAL.print(CMD);
    Serial.println(CMD);
    HWSERIAL.flush();
    Serial.flush();

  
  long t0=millis();
  while (( millis() - t0 ) < 500) {
	if (HWSERIAL.available() > 0) {
    int n = HWSERIAL.readBytes(buf,64);
    for(i=0;i<n;i++) {
      Serial.print(buf[i]);
    }
    Serial.println();
	}
  }
}
