#include <timer.h>
#include "ServoTimer2.h"
#include <L298N.h>                  // used to drive motor

#define UTRASONIC_SERVO_PIN   11    // Servo is attached to digital pin 11
#define UTRASONIC_TRIG_PIN    A0    // Ultrasonic trigger pin is attached to Analog 0, why ...
#define UTRASONIC_ECHO_PIN    A1    // Ultrasonic echo pin is attached to Analog 1, also why ...
#define UTRASONIC_TIMING_MOVE 250   // 250 ms is a safe timing to move the servo
#define UTRASONIC_TIMING_MEAS 10    // we measure distance 10 ms before next servo move

// Right Motor
#define ENA 5
#define IN1 6
#define IN2 7
// Left Motor
#define IN3 8
#define IN4 9
#define ENB 10

L298N motor1(ENA, IN1, IN2);
L298N motor2(ENB, IN3, IN4);

Timer<3> timer;                            // List of three timer ms based: debug, move, measure
ServoTimer2 ultrasonic_servo;              // Create servo using timer2 object to control the ultrasonic servo

float ultrasonic_measures[5] = {0.0,0.0,0.0,0.0,0.0}; // init list of measures to be safe
short servo_direction = 1;                 // Initial direction positive to move clockwise
short servo_position  = 2;                 // Initial position is middle

float measure_ultrasonic_distance() {
  digitalWrite(UTRASONIC_TRIG_PIN, LOW);   // set trig port low level for 2μs
  delayMicroseconds(2);
  digitalWrite(UTRASONIC_TRIG_PIN, HIGH);  // set trig port high level for 10μs (at least 10μs)
  delayMicroseconds(10);
  digitalWrite(UTRASONIC_TRIG_PIN, LOW);   // set trig port low level
  return pulseIn(UTRASONIC_ECHO_PIN, HIGH, 7000) / 58.273;  // timeout around 100 cm 
}

bool debug_print(void *) {
  Serial.print(ultrasonic_measures[0]);
  Serial.print("\t");
  Serial.print(ultrasonic_measures[1]);
  Serial.print("\t");
  Serial.print(ultrasonic_measures[2]);
  Serial.print("\t");
  Serial.print(ultrasonic_measures[3]);
  Serial.print("\t");
  Serial.println(ultrasonic_measures[4]);
  return true;
}

bool save_measure(void *) {
  // Do two measures and save the highest at the current position
  float m1 = measure_ultrasonic_distance();
  float m2 = measure_ultrasonic_distance();
  ultrasonic_measures[servo_position] = (m1 > m2) ? m1: m2;
  return true;
}

void move_servo() {
  short servo_angles[5] = {2080, 1810, 1540, 1270, 1000}; // -60 -30 0 30 60 degree 
  ultrasonic_servo.write(servo_angles[servo_position]);
}

bool move_and_measure(void *) {
  servo_position = servo_position + 1 * servo_direction;
  if(servo_position == 4) servo_direction = -1;           // If we arrive at the right of the movement we go counter-clock
  if(servo_position == 0) servo_direction =  1;           // If we arrive at the left of the movement we go clock-wise

  move_servo();
  timer.in(UTRASONIC_TIMING_MOVE - UTRASONIC_TIMING_MEAS, save_measure);  // In 240 ms we do a measure just before next movement
  return true;
}

void setup() {
  Serial.begin(115200);                         // Start serial 115200

  pinMode(UTRASONIC_ECHO_PIN, INPUT);           // Set Ultrasonic echo port as input
  pinMode(UTRASONIC_TRIG_PIN, OUTPUT);          // Set Ultrasonic trig port as input
  digitalWrite(UTRASONIC_TRIG_PIN, LOW);        // set trig port low

  ultrasonic_servo.attach(UTRASONIC_SERVO_PIN); // Attaches the servo on pin 11
  move_servo();                                 // Move to middle position
  
  timer.every(UTRASONIC_TIMING_MOVE, move_and_measure); // Start debug speed timer every 100 ms
  timer.every(UTRASONIC_TIMING_MOVE*5, debug_print);    // Start debug speed timer every 100 ms

  motor1.setSpeed(200);                         // Move motor at medium speed
  motor2.setSpeed(200);                         // Move motor at medium speed
  motor1.forward();                             // Enable motor 
  motor2.forward();                             // Enable motor 
}

void loop() {
  timer.tick();                                 // tick the timer
}
