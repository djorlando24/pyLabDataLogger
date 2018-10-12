/*
   Hall Effect Flow Meter pulse counter
   
   Read Water Flow Meter and output reading to USI SPI
   on ATTiny. 
   
   Pulse frequency (Hz) = 7.5Q, Q is flow rate in L/min. (Results in +/- 3% range).
   The flowrate is litres_per_hour = flow_frequency * 60 / 7.5
   where flow_frequency is the number of counts per n_flush*dt_ms milliseconds.

   D Duke
   Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
   Monash University, Australia
*/

#define SIG   PB4  // signal input
#define CS    PB3  // Chip select
#define DO    PB1  // MISO
#define DI    PB0  // MOSI
#define USCK  PB2  // Clock
#define dt_ms 500 // frequency of buffer updates in main loop
#define n_flush 10 // how frequently to reset the counter (n*dt_ms)

volatile char reqID = 0;       // This is for the first byte we receive, which is intended to be the request identifier
volatile uint8_t index = 0;    // this is to send back the right element in the array
volatile uint8_t m_nPinALast = PINB; // pin states for interrupt differentiation
volatile unsigned int  flow_frequency = 0;  // Counts pulses
volatile unsigned int flow_buffer = 0;      // Count rate per n_flush*dt_ms
unsigned long current_time;    // millisecond clock now
unsigned long cloop_time;      // millisecond clock when last started loop
unsigned int n_buf_upd = 0; // count buffer updates

byte * fPTR = (byte*) &flow_buffer; // pointer on the variable to transmit

// Interrupt function for frequency counter and CS.
ISR(PCINT0_vect) 
{ 
   // Latch the current pin values and deltas
   uint8_t nPinValCur = PINB;
   uint8_t nPinValChg = nPinValCur ^ m_nPinALast;

   // counting the input signal
   if (nPinValChg & (1 << SIG)) {
      if (nPinValCur & (1<<SIG)) {
        flow_frequency++;
      }
   }

   // CS pin
   if (nPinValChg & (1 << CS)) { 
      if (nPinValCur & (1 << CS)) { // rising edge
        // If edge is rising, turn the 4-bit overflow interrupt off:
        USICR &= ~(1<<USIOIE);
      } else {
        // Falling edge CS
        // the command and index variables shall be initialized
        // and the 4-bit overflow counter of the USI communication shall be activated:
        reqID = 0;
        index = 0;
        USICR |= (1<<USIOIE);
        USISR = 1<<USIOIF;      // Clear Overflow bit
     }
   } 

   m_nPinALast = nPinValCur;
}

// USI interrupt routine. Always executed when 4-bit overflows (after 16 clock edges = 8 clock cycles):
ISR(USI_OVF_vect)
{
  /*switch(reqID){
    case 0: // If reqID value is zero (just initialized), then first message is the reqID.
          reqID = USIDR;      // Read in from USIDR register
          USISR = 1<<USIOIF;  // Clear Overflow bit

    case 1:*/
          // Write value to send back into USIDR and clear the overflow bit:
          USIDR = fPTR[index];
          USISR = 1<<USIOIF;
          index++;            // Increment index to transmit the following element next
          if (index>4) index=0; // Loop
 /*         break;
          
    default: // Send 'reqID' back for debugging.
          USIDR = reqID;
          USISR = 1<<USIOIF;
          break;
  }*/
}

void setup()
{ 
   cli();                             // disable interrupts
   DDRB |= 1<<DO;                     // MISO Pin has to be an output. Inputs are set by default.
   USICR = ((1<<USIWM0)|(1<<USICS1)); // Activate 3- Wire Mode and use of external
                                      // clock but NOT the interrupt at the Counter overflow (USIOIE)
   PORTB |= 1<<CS;                    // Activate Pull-Up resistor on CS
   PCMSK|=(1<<CS);                    // Active Interrupt on CS
   PCMSK|=(1<<SIG);                   // Activate interrupt on trigger signal
   GIMSK|=1<<PCIE;                    // General Interrupt Mask Register / PCIE bit activates external interrupts
   
   current_time=millis();              // set clock for counter
   cloop_time = current_time;
   delay(500);
   
   sei();                             // enable interrupts
} 

void loop ()    
{
   current_time = millis();
   // Every dt_ms, buffer the value
   if(current_time >= (cloop_time + dt_ms))
   {     
      cloop_time = current_time;            // Updates cloopTime
      flow_buffer = int(flow_frequency);         // Buffer the counts per dt_ms
      n_buf_upd++;
   }

   if (n_buf_upd>=n_flush) {
      flow_frequency = 0;                   // Reset Counter
      n_buf_upd=0;
   }
   
}
