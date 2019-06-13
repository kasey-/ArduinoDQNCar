#include <timer.h>                  // https://github.com/contrem/arduino-timer
#include "ServoTimer2.h"            // https://github.com/nabontra/ServoTimer2
#include <L298N.h>                  // https://github.com/AndreaLombardo/L298N
#include <EnableInterrupt.h>        // https://github.com/GreyGnome/EnableInterrupt
#include <Ultrasonic.h>             // https://github.com/ErickSimoes/Ultrasonic

#define DIST_SENS_RIGHT_PIN A4
#define DIST_SENS_LEFT_PIN  A5

#define UTRASONIC_SERVO_PIN   11    // Servo is attached to digital pin 11
#define UTRASONIC_TRIG_PIN    A0    // Ultrasonic trigger pin is attached to Analog 0, why ...
#define UTRASONIC_ECHO_PIN    A1    // Ultrasonic echo pin is attached to Analog 1, also why ...
#define UTRASONIC_TIMING_MOVE 250   // 250 ms is a safe timing to move the servo
#define UTRASONIC_TIMING_MEAS 10    // we measure distance 10 ms before next servo move
#define UTRASONIC_TIMEOUT     5700UL// Ultrasonic timeout 7 000 = 1m

#define SAFETY_TIMING         50    // we measure distance 10 ms before next servo move
#define BACKWARD_DELAY        2500  // Move backward after collision 2.5 s

// Right Motor
#define ENA 5
#define IN1 6
#define IN2 7
// Left Motor
#define IN3 8
#define IN4 9
#define ENB 10
// Motor settings
#define MOTOR_SPEED 0

#define PENALTY_TURN  -0.8
#define PENALTY_DIST  -0.7
#define PENALTY_CRASH -500.0
#define BONUS_MOVE    0.5

L298N motor1(ENA, IN1, IN2);
L298N motor2(ENB, IN3, IN4);

Timer<5> timer;                            // List of three timer ms based: move, compute reward, safety, ...
ServoTimer2 ultrasonic_servo;              // Create servo using timer2 object to control the ultrasonic servo
Ultrasonic  ultrasonic_sensor(UTRASONIC_TRIG_PIN, UTRASONIC_ECHO_PIN, UTRASONIC_TIMEOUT);

bool car_is_crashed;
float _partial_reward;

float ultrasonic_measures[3] = {1.0,1.0,1.0}; // init list of measures to be safe
short servo_direction = 1;                 // Initial direction positive to move clockwise
short servo_position  = 1;                 // Initial position is middle

bool check_if_crashed(void *) {
  if(!digitalRead(DIST_SENS_RIGHT_PIN) || !digitalRead(DIST_SENS_LEFT_PIN)) {
    car_is_crashed = true;      
    motor1.stop();                             
    motor2.stop();                           
  } else {
    car_is_crashed = false;  
  }
  return true;
}

bool save_measure(void *) {
  // Do two measures and save the highest at the current position
  float m1 = ultrasonic_sensor.read(CM) / 103.0;
  float m2 = ultrasonic_sensor.read(CM) / 103.0;
  ultrasonic_measures[servo_position] = (m1 < m2) ? m1 : m2;
  return true;
}

void move_servo() {
  //short servo_angles[3] = {1970, 1540, 1150}; // -45 0 45 degree 
  short servo_angles[3] = {1540, 1540, 1540}; // -45 0 45 degree 
  ultrasonic_servo.write(servo_angles[servo_position]);
}

bool move_and_measure(void *) {
  servo_position = servo_position + 1 * servo_direction;
  if(servo_position == 2) servo_direction = -1;           // If we arrive at the right of the movement we go counter-clock
  if(servo_position == 0) servo_direction =  1;           // If we arrive at the left of the movement we go clock-wise

  move_servo();
  timer.in(UTRASONIC_TIMING_MOVE - UTRASONIC_TIMING_MEAS, save_measure);  // In 240 ms we do a measure just before next movement
  return true;
}

bool debug_sensor(void *) {
  print_sensors();
  Serial.println("");
  return true;
}

void print_sensors() {
  for(int i = 0; i < 3; i++) {
    Serial.print(ultrasonic_measures[i],DEC);
    Serial.print(',');
  }
  Serial.print(!digitalRead(DIST_SENS_LEFT_PIN),DEC);
  Serial.print(',');
  Serial.print(!digitalRead(DIST_SENS_RIGHT_PIN),DEC);
}

void reset_car() {
  if(car_is_crashed) {
    motor1.setSpeed(MOTOR_SPEED);                 // Move motors at medium speed
    motor2.setSpeed(MOTOR_SPEED);
    motor1.backward();                            // Move motors backward to go out of collision
    motor2.backward();
    delay(BACKWARD_DELAY);                        // Move for 2.5s
  }
  motor1.stop();                                // Stop Motor to wait next instruction
  motor2.stop();                                
  car_is_crashed  = false;
  print_sensors();
  Serial.println("");
}

void step(int action) {  
  if(car_is_crashed) {
    print_sensors();
    Serial.print(",");
    Serial.println(PENALTY_CRASH,DEC);
    motor1.stop();                                // Stop Left Motor
    motor2.stop();                                // Stop Left Motor
    return;  
  }
    
  switch(action) {
    case 0: // Turn left
      _partial_reward = PENALTY_TURN;
      motor2.stop();                                // Stop Left Motor
      motor1.setSpeed(MOTOR_SPEED);                 // Move Right Motor at medium speed
      motor1.forward();                             // Enable Right motor 
    break;
    case 1: // Turn Right
      _partial_reward = PENALTY_TURN;
      motor1.stop();                                // Stop Right Motor
      motor2.setSpeed(MOTOR_SPEED);                 // Move Left Motor at medium speed
      motor2.forward();                             // Enable Left motor
    break;
    case 2: // Forward
      _partial_reward = BONUS_MOVE;
      motor1.setSpeed(MOTOR_SPEED);                 // Move Right motor at medium speed
      motor2.setSpeed(MOTOR_SPEED);                 // Move Left motor at medium speed
      motor1.forward();                             // Enable Right motor 
      motor2.forward();                             // Enable Left motor     
    break;
  }
  
  timer.in(UTRASONIC_TIMING_MOVE*3, [](void*) -> bool {
    for(int i = 0; i < 3; i++)
      _partial_reward += (0.9 - ultrasonic_measures[i]) / 3.0;
    print_sensors();
    Serial.print(',');
    Serial.println(_partial_reward,DEC);
    return false;
  });
}

void setup() {
  Serial.begin(115200);                         // Start serial 115200

  pinMode(DIST_SENS_RIGHT_PIN, INPUT);
  pinMode(DIST_SENS_LEFT_PIN, INPUT);

  pinMode(UTRASONIC_ECHO_PIN, INPUT);           // Set Ultrasonic echo port as input
  pinMode(UTRASONIC_TRIG_PIN, OUTPUT);          // Set Ultrasonic trig port as input
  digitalWrite(UTRASONIC_TRIG_PIN, LOW);        // set trig port low

  _partial_reward = 0.0;
  car_is_crashed = false;
  ultrasonic_servo.attach(UTRASONIC_SERVO_PIN); // Attaches the servo on pin 11
  move_servo();                                 // Move to middle position

  enableInterrupt(DIST_SENS_RIGHT_PIN, check_if_crashed, FALLING);
  enableInterrupt(DIST_SENS_LEFT_PIN,  check_if_crashed, FALLING);
  
  timer.every(UTRASONIC_TIMING_MOVE, move_and_measure); // Start debug speed timer every  250 ms
  timer.every(SAFETY_TIMING, check_if_crashed);         // Check every 50 ms if crashed
    
  motor1.stop();                                // Disable motor 
  motor2.stop();                                // Disable motor
}

void loop() {
  timer.tick();                                 // tick the timer
  if (Serial.available() > 0) {
    int _cmd = Serial.parseInt();
    switch(_cmd) {
      case -1:
        reset_car();
      break;
      case 0:
      case 1:
      case 2:      
        step(_cmd);
    }
    Serial.flush();
  }
}
