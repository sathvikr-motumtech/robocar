#include <IRremote.hpp>

#define IR_RECEIVE_PIN 11


// --- Motor Control Pin Definitions ---
#define ENA 3
#define IN1 2
#define IN2 4
#define IN3 7
#define IN4 8
#define ENB 9

// How long to move per button press (in milliseconds)
int moveDuration = 500; 
int turnDuration = 300;

void setup() {
  Serial.begin(9600);
  // Start the IR receiver
  IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK);
  
  // Set motor pins as outputs
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENB, OUTPUT);

  Serial.println("Ready! get, set, go!");
}

void loop() {
  // Check if an IR code has been received
  if (IrReceiver.decode()) {
    Serial.print("Received the code: ");
    Serial.println(IrReceiver.decodedIRData.decodedRawData, HEX);
    // Use an if...else if chain to check the 64-bit raw data, switch is not working!
    if (IrReceiver.decodedIRData.decodedRawData == 0xF609FF00) { // UP Arrow
      Serial.println("Moving forward now ...");
      moveForward();
    } else if (IrReceiver.decodedIRData.decodedRawData == 0xF807FF00) { // DOWN Arrow
      moveBackward();
    } else if (IrReceiver.decodedIRData.decodedRawData == 0xBB44FF00) { // LEFT Arrow
      turnLeft();
    } else if (IrReceiver.decodedIRData.decodedRawData == 0xBC43FF00) { // RIGHT Arrow
      turnRight();
    } else if (IrReceiver.decodedIRData.decodedRawData == 0xBF40FF00) { // OK Button
      stopRobot();
    } else {
      Serial.println("Unknown code!");
      Serial.println(IrReceiver.decodedIRData.decodedRawData, HEX);
    }
    
    // Resume receiving for the next button press
    IrReceiver.resume(); 
  }
}
// --- Movement Functions ---

void moveForward() {
  analogWrite(ENA, 200);
  analogWrite(ENB, 200);
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  delay(moveDuration); // Move for a fixed time
  stopRobot();
}

void moveBackward() {
  analogWrite(ENA, 200);
  analogWrite(ENB, 200);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  delay(moveDuration);
  stopRobot();
}

void turnLeft() {
  analogWrite(ENA, 200);
  analogWrite(ENB, 200);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  delay(turnDuration);
  stopRobot();
}

void turnRight() {
  analogWrite(ENA, 200);
  analogWrite(ENB, 200);
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  delay(turnDuration);
  stopRobot();
}

void stopRobot() {
  Serial.println("Stopping Robot!");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}
