#include <IRremote.hpp>

#define IR_RECEIVE_PIN 11

// --- Motor Driver 1 (Left Side) Pin Definitions ---
#define ENA1 3   // Enable A for Driver 1
#define IN1_1 2  // Input 1 for Driver 1
#define IN2_1 4  // Input 2 for Driver 1
#define IN3_1 7  // Input 3 for Driver 1  
#define IN4_1 8  // Input 4 for Driver 1
#define ENB1 9   // Enable B for Driver 1

// --- Motor Driver 2 (Right Side) Pin Definitions ---
#define ENA2 5   // Enable A for Driver 2
#define IN1_2 6  // Input 1 for Driver 2
#define IN2_2 10 // Input 2 for Driver 2
#define IN3_2 12 // Input 3 for Driver 2
#define IN4_2 13 // Input 4 for Driver 2
#define ENB2 A0  // Enable B for Driver 2 (using analog pin as digital)

// --- Pre-defined movement durations ---
int moveDuration = 500; 
int turnDuration = 300;

void setup() {
  Serial.begin(9600);
  
  // Initialize Motor Driver 1 pins
  pinMode(ENA1, OUTPUT);
  pinMode(IN1_1, OUTPUT);
  pinMode(IN2_1, OUTPUT);
  pinMode(IN3_1, OUTPUT);
  pinMode(IN4_1, OUTPUT);
  pinMode(ENB1, OUTPUT);
  
  // Initialize Motor Driver 2 pins
  pinMode(ENA2, OUTPUT);
  pinMode(IN1_2, OUTPUT);
  pinMode(IN2_2, OUTPUT);
  pinMode(IN3_2, OUTPUT);
  pinMode(IN4_2, OUTPUT);
  pinMode(ENB2, OUTPUT);
  
  // Ensure all motors are OFF at startup
  stopRobot();
  delay(100);
  
  // Start the IR receiver AFTER motors are initialized
  IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK);
  
  Serial.println("Ready get set go! (4-wheel drive ready)");
}

void loop() {
  // Check if an IR code has been received
  if (IrReceiver.decode()) {
    Serial.print("Received the code: ");
    Serial.println(IrReceiver.decodedIRData.decodedRawData, HEX);
    
    // Process the command
    processIRCommand();
    
    // CRITICAL: Add delay before resuming to prevent interference
    delay(50);
    IrReceiver.resume(); 
    
    // Additional delay to let IR receiver stabilize
    delay(50);
  }
}

void processIRCommand() {
  switch(IrReceiver.decodedIRData.decodedRawData) {
    case 0xF609FF00: // UP Arrow
      Serial.println("Moving forward now ...");
      moveForward();
      break;
      
    case 0xF807FF00: // DOWN Arrow
      Serial.println("Moving backward now ...");
      moveBackward();
      break;
      
    case 0xBB44FF00: // LEFT Arrow
      Serial.println("Turning left now ...");
      turnLeft();
      break;
      
    case 0xBC43FF00: // RIGHT Arrow
      Serial.println("Turning right now ...");
      turnRight();
      break;
      
    case 0xBF40FF00: // OK Button
      Serial.println("Stop command received ...");
      stopRobot();
      break;
      
    default:
      Serial.println("Unknown code!");
      Serial.println(IrReceiver.decodedIRData.decodedRawData, HEX);
      break;
  }
}

// --- 4-Wheel Movement Functions ---

void moveForward() {
  IrReceiver.stop();
  
  // Driver 1 - Left side motors forward
  analogWrite(ENA1, 255);
  analogWrite(ENB1, 255);
  digitalWrite(IN1_1, HIGH);
  digitalWrite(IN2_1, LOW);
  digitalWrite(IN3_1, HIGH);
  digitalWrite(IN4_1, LOW);
  
  // Driver 2 - Right side motors forward
  analogWrite(ENA2, 255);
  digitalWrite(ENB2, HIGH);
  digitalWrite(IN1_2, HIGH);
  digitalWrite(IN2_2, LOW);
  digitalWrite(IN3_2, HIGH);
  digitalWrite(IN4_2, LOW);
  
  delay(moveDuration);
  stopRobot();
  
  delay(100);
  IrReceiver.start();
}

void moveBackward() {
  IrReceiver.stop();
  
  // Driver 1 - Left side motors backward
  analogWrite(ENA1, 255);
  analogWrite(ENB1, 255);
  digitalWrite(IN1_1, LOW);
  digitalWrite(IN2_1, HIGH);
  digitalWrite(IN3_1, LOW);
  digitalWrite(IN4_1, HIGH);
  
  // Driver 2 - Right side motors backward
  analogWrite(ENA2, 255);
  digitalWrite(ENB2, HIGH);
  digitalWrite(IN1_2, LOW);
  digitalWrite(IN2_2, HIGH);
  digitalWrite(IN3_2, LOW);
  digitalWrite(IN4_2, HIGH);
  
  delay(moveDuration);
  stopRobot();
  
  delay(100);
  IrReceiver.start();
}

void turnLeft() {
  IrReceiver.stop();
  
  // Driver 1 - Left side motors backward
  analogWrite(ENA1, 255);
  analogWrite(ENB1, 255);
  digitalWrite(IN1_1, LOW);
  digitalWrite(IN2_1, HIGH);
  digitalWrite(IN3_1, LOW);
  digitalWrite(IN4_1, HIGH);
  
  // Driver 2 - Right side motors forward
  analogWrite(ENA2, 255);
  digitalWrite(ENB2, HIGH);
  digitalWrite(IN1_2, HIGH);
  digitalWrite(IN2_2, LOW);
  digitalWrite(IN3_2, HIGH);
  digitalWrite(IN4_2, LOW);
  
  delay(turnDuration);
  stopRobot();
  
  delay(100);
  IrReceiver.start();
}

void turnRight() {
  IrReceiver.stop();
  
  // Driver 1 - Left side motors forward
  analogWrite(ENA1, 255);
  analogWrite(ENB1, 255);
  digitalWrite(IN1_1, HIGH);
  digitalWrite(IN2_1, LOW);
  digitalWrite(IN3_1, HIGH);
  digitalWrite(IN4_1, LOW);
  
  // Driver 2 - Right side motors backward
  analogWrite(ENA2, 255);
  digitalWrite(ENB2, HIGH);
  digitalWrite(IN1_2, LOW);
  digitalWrite(IN2_2, HIGH);
  digitalWrite(IN3_2, LOW);
  digitalWrite(IN4_2, HIGH);
  
  delay(turnDuration);
  stopRobot();
  
  delay(100);
  IrReceiver.start();
}

void stopRobot() {
  Serial.println("Stopping Robot!");
  
  // Stop Motor Driver 1
  digitalWrite(IN1_1, LOW);
  digitalWrite(IN2_1, LOW);
  digitalWrite(IN3_1, LOW);
  digitalWrite(IN4_1, LOW);
  analogWrite(ENA1, 0);
  analogWrite(ENB1, 0);
  
  // Stop Motor Driver 2
  digitalWrite(IN1_2, LOW);
  digitalWrite(IN2_2, LOW);
  digitalWrite(IN3_2, LOW);
  digitalWrite(IN4_2, LOW);
  analogWrite(ENA2, 0);
  digitalWrite(ENB2, LOW);
}
