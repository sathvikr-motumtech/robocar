/*
 * An IR code finder for modern IRremote library (v3+)
 */
#include <IRremote.hpp>

// Define the pin for the IR receiver
#define IR_RECEIVE_PIN 11

void setup() {
  Serial.begin(9600);
  // Start the receiver
  IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK); // ENABLE_LED_FEEDBACK blinks the built-in LED on pin 13
  Serial.println("Ready to receive IR codes ...");
}

void loop() {
  // Check if a signal has been received
  if (IrReceiver.decode()) {
    Serial.println("---------------------------------");
    // Print a summary of the received data
    IrReceiver.printIRResultShort(&Serial);

    Serial.print("Raw Hex Code to Use: ");
    Serial.println(IrReceiver.decodedIRData.decodedRawData, HEX);
    
    Serial.println("---------------------------------");

    // Resume receiving the next signal
    IrReceiver.resume(); 
  }
}
