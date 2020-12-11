/* Read hall effect sensors and report switching frequency.
 *  Read HX711 load cell amplifier while doing so.
 *  For Arduino Pro Micro 16MHz/5V 
 *  
 *  The output wires for TTL UART at 9600bps:
 *  black = GND
 *  white = 5V
 *  Gray = TXD
 *  Purple = RXD
 *  Blue = Reset
 *  
 *  D Duke
 *  11/12/2020
*/

// hall effect sensor setup

#define input0 2 // interruptable pin
#define input1 3 // interruptable pin
#define pwmout 9 // pwm output (for debugging)
#define txled 13 // light when writing to serial
#define pwm_rpmmax 3000.0 // value that corresponds to max pwm output
#define rpm_coeff 6e7 // Multiplication factor is 1 rev/triggers * 1e6 us/s * 60 s/min
#define ring_buffer_size 16 // averaging buffer
#define maxwait 1e6 // how long to wait after last trigger before flushing the buffer
#define big 4000000000 // delay between pulses corresponding to minimum RPM reading
#define update_pwm_every 8 // how often to refresh pwm output
#define print_every 1024 // how often to write to serial

unsigned long t0_input0;
unsigned long t1_input0;
unsigned long dt_input0_buf[ring_buffer_size];
float dt_input0 = big;
int nbuf_input0 = 0;

unsigned long t0_input1;
unsigned long t1_input1;
unsigned long dt_input1_buf[ring_buffer_size];
float dt_input1 = big;
int nbuf_input1 = 0;
float pwmval = 0;

int i;
int counter=0;

// scale setup

#include "HX711.h"
HX711 scale;
uint8_t dataPin = A1;
uint8_t clockPin = A0;
#define SCALE_UNIT "g"

void setup() {
    // Initialize buffer
    for (i=0;i<ring_buffer_size;i++) {
        dt_input0_buf[i]=big;
        dt_input1_buf[i]=big;
    }
    // Init timestamps
    t0_input0 = micros();
    t1_input0 = t0_input0 + big;
    t0_input1 = micros();
    t1_input1 = t0_input1 + big;
    
    // Setup IO
    pinMode(input0,INPUT_PULLUP);
    attachInterrupt(INT0,ISR_input0,FALLING); // removed digitalPinToInterrupt for Teensy
    
    pinMode(input1,INPUT_PULLUP);
    attachInterrupt(INT1,ISR_input1,FALLING); // removed digitalPinToInterrupt for Teensy

    pinMode(pwmout,OUTPUT);
    pinMode(txled,OUTPUT);
    analogWrite(pwmout,0);
    digitalWrite(txled,LOW);


    scale.begin(dataPin, clockPin);
    // loadcell factor 20 KG
    scale.set_scale(100.);//127.15);
    scale.tare();
    
    Serial.begin(9600);
}

void loop() {
    // if no interrupt after some time, reset timestamps to read ~zero freq.
    if ((micros() - t1_input0) > maxwait) {
        t0_input0 = micros();
        t1_input0 = t0_input0 + big;
    }
    if ((micros() - t1_input1) > maxwait) {
        t0_input1 = micros();
        t1_input1 = t0_input1 + big;
    }
    
    // Write current delay period to ring buffer
    dt_input0_buf[nbuf_input0] = t1_input0 - t0_input0;
    nbuf_input0 = (nbuf_input0 + 1)%ring_buffer_size;
    
    dt_input1_buf[nbuf_input1] = t1_input1 - t0_input1;
    nbuf_input1 = (nbuf_input1 + 1)%ring_buffer_size;
    
    // Compute average and display to serial
    if (counter%print_every == 0) {
    
        // Compute average from ring buffer
        dt_input0 = 0;
        dt_input1 = 0;
        for (i=0;i<ring_buffer_size;i++) {
            dt_input0 += dt_input0_buf[i]/(float)ring_buffer_size;
            dt_input1 += dt_input1_buf[i]/(float)ring_buffer_size;
        }

        
        // Compute frequency and write RPM.
        digitalWrite(txled,HIGH);
        Serial.print("Stirrer_Scale: RPM0 = ");
        Serial.print(rpm_coeff / dt_input0);
        Serial.print(" rpm, RPM1 = ");
        Serial.print(rpm_coeff / dt_input1);
        Serial.print(" rpm, WEIGHT =");
        Serial.print(scale.get_units(10));
        Serial.print(" ");
        Serial.println(SCALE_UNIT);
        digitalWrite(txled,LOW);
        
        delay(10); // prevent excessively frequent writing to serial port
        counter=0;
        
    }

    // update input0 value to pwm
    if (counter%update_pwm_every == 0) {
    
        // Compute average from ring buffer
        dt_input0=0;
        //dt_input1=0;
        for (i=0;i<ring_buffer_size;i++) {
            dt_input0 += dt_input0_buf[i]/(float)ring_buffer_size;
            //dt_input1 += dt_input1_buf[i]/(float)ring_buffer_size;
        }
    
        // update PWM with input0 value
        pwmval =  255 * rpm_coeff / dt_input0 / pwm_rpmmax;
        if (pwmval > 255) pwmval=255;
        if (pwmval < 0) pwmval=0;
        analogWrite(pwmout, (int)pwmval);

    }
    
    delayMicroseconds(10);
    counter++;
}

// ISR for sensor on pin input0
// Update interrupt time stamps
void ISR_input0() {
    t0_input0 = t1_input0;
    t1_input0 = micros();
}

// ISR for sensor on pin input1
// Update interrupt time stamps
void ISR_input1() {
    t0_input1 = t1_input1;
    t1_input1 = micros();
}
