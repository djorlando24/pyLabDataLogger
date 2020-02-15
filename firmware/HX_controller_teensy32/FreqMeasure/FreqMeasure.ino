#include <FreqMeasure.h>

long i=0;

void setup() {
  // put your setup code here, to run once:
  pinMode(3, INPUT_PULLUP);
  FreqMeasure.begin();
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.print(i);
  Serial.print(": ");
  Serial.println(FreqMeasure.countToFrequency(FreqMeasure.read()));
  delay(100);
  i+=1;
}
