#include <timer.h>                   // https://github.com/contrem/arduino-timer
#include "ServoTimer2.h"             // https://github.com/nabontra/ServoTimer2
#include <L298N.h>                   // https://github.com/AndreaLombardo/L298N
#include <EnableInterrupt.h>         // https://github.com/GreyGnome/EnableInterrupt
#include <Ultrasonic.h>              // https://github.com/ErickSimoes/Ultrasonic

#define DIST_SENS_RIGHT_PIN A4
#define DIST_SENS_LEFT_PIN  A5

#define UTRASONIC_SERVO_PIN   11     // Servo is attached to digital pin 11
#define UTRASONIC_TRIG_PIN    A0     // Ultrasonic trigger pin is attached to Analog 0, why ...
#define UTRASONIC_ECHO_PIN    A1     // Ultrasonic echo pin is attached to Analog 1, also why ...
#define UTRASONIC_TIMING_MOVE 250    // 250 ms is a safe timing to move the servo
#define UTRASONIC_TIMING_MEAS 10     // we measure distance 10 ms before next servo move
#define UTRASONIC_TIMEOUT     5700UL // Ultrasonic timeout 7 000 = 1m

#define HANDLE_CMD_TIMING     10

#define SAFETY_TIMING         50     // we measure distance 10 ms before next servo move
#define SAFETY_CMD_DELAY      3500   // Stop the car if we did not received a cmd since 3.5s
#define BACKWARD_DELAY        2000   // Move backward after collision 2.5 s

// Right Motor
#define ENA 5
#define IN1 6
#define IN2 7
// Left Motor
#define IN3 8
#define IN4 9
#define ENB 10
// Motor settings
#define MOTOR_SPEED 80

#define PENALTY_TURN  -0.8
#define PENALTY_DIST  -0.7
#define PENALTY_CRASH -500.0
#define BONUS_MOVE    0.5

L298N motor1(ENA, IN1, IN2);
L298N motor2(ENB, IN3, IN4);

Timer<16> timer;                           // List of three timer ms based: move, compute reward, safety, ...
ServoTimer2 ultrasonic_servo;              // Create servo using timer2 object to control the ultrasonic servo
Ultrasonic  ultrasonic_sensor(UTRASONIC_TRIG_PIN, UTRASONIC_ECHO_PIN, UTRASONIC_TIMEOUT);

bool car_is_crashed;
float _partial_reward;
bool _lock_cmd;
unsigned long send_result_time;
unsigned long last_cmd_time;

float ultrasonic_measures[3] = {1.0,1.0,1.0}; // init list of measures to be safe
short servo_direction = 1;                 // Initial direction positive to move clockwise
short servo_position  = 1;                 // Initial position is middle

void update_cmd_timer() {
  last_cmd_time = millis();
}

bool do_security_check(void *) {
  if(
      !digitalRead(DIST_SENS_RIGHT_PIN) ||
      !digitalRead(DIST_SENS_LEFT_PIN)
    ) {
    car_is_crashed = true;      
    motor1.stop();
    motor2.stop();
  } else {
    if(last_cmd_time + SAFETY_CMD_DELAY < millis()) {
      motor1.stop();                       // Stop Motor to wait next instruction
      motor2.stop();
    }
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
  short servo_angles[3] = {1970, 1540, 1150}; // -45 0 45 degree 
  //short servo_angles[3] = {1540, 1540, 1540}; // -45 0 45 degree 
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
    disable_dist_int();
    motor1.setSpeed(MOTOR_SPEED);                 // Move motors at medium speed
    motor2.setSpeed(MOTOR_SPEED);
    motor1.backward();                            // Move motors backward to go out of collision
    motor2.backward();
    delay(BACKWARD_DELAY);                        // Move for 2.5s
    enable_dist_int();
  }
  motor1.stop();                                // Stop Motor to wait next instruction
  motor2.stop();                                
  car_is_crashed  = false;
  _lock_cmd = false;
  print_sensors();
  Serial.println("");
}

bool send_ultrasonic_measure(void *) {
  if(send_result_time == 0.0)
    return true;
  if(send_result_time > millis())
    return true;
  for(int i = 0; i < 3; i++)
    _partial_reward += (0.9 - ultrasonic_measures[i]) / 3.0;
  print_sensors();
  Serial.print(',');
  Serial.println(_partial_reward,DEC);
  send_result_time = 0.0;
  _lock_cmd = false;
  return true;
}

void step(int action) {  
  if(car_is_crashed) {
    print_sensors();
    Serial.print(",");
    Serial.println(PENALTY_CRASH,DEC);
    motor1.stop();                                // Stop Left Motor
    motor2.stop();                                // Stop Left Motor
    _lock_cmd = false;
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

  send_result_time = millis() + 750;
}

bool handle_cmd(void *) {
  if (Serial.available() > 0 && ! _lock_cmd) {
    update_cmd_timer();
    _lock_cmd = true;
    int _cmd = Serial.parseInt();
    switch(_cmd) {
      case -1:
        reset_car();
      break;
      case 0:
      case 1:
      case 2:
        step(_cmd);
      default:
        _lock_cmd = false;  
    }
  }
  return true;
}

void disable_dist_int() {
  disableInterrupt(DIST_SENS_RIGHT_PIN);
  disableInterrupt(DIST_SENS_LEFT_PIN);
}

void enable_dist_int() {
  enableInterrupt(DIST_SENS_RIGHT_PIN, do_security_check, FALLING);
  enableInterrupt(DIST_SENS_LEFT_PIN,  do_security_check, FALLING);
}

void setup() {
  Serial.begin(115200);                         // Start serial 115200
  Serial.setTimeout(10);                        // Serial timeout = 10 ms otherwise Parseint wait 1s '-_-

  pinMode(DIST_SENS_RIGHT_PIN, INPUT);
  pinMode(DIST_SENS_LEFT_PIN, INPUT);

  pinMode(UTRASONIC_ECHO_PIN, INPUT);           // Set Ultrasonic echo port as input
  pinMode(UTRASONIC_TRIG_PIN, OUTPUT);          // Set Ultrasonic trig port as input
  digitalWrite(UTRASONIC_TRIG_PIN, LOW);        // set trig port low

  update_cmd_timer();
  _partial_reward = 0.0;
  _lock_cmd = false;
  car_is_crashed = false;
  send_result_time = 0.0;
  ultrasonic_servo.attach(UTRASONIC_SERVO_PIN); // Attaches the servo on pin 11
  move_servo();                                 // Move to middle position

  enable_dist_int();
  
  timer.every(UTRASONIC_TIMING_MOVE, move_and_measure); // Start debug speed timer every  250 ms
  timer.every(SAFETY_TIMING, do_security_check);        // Check every 50 ms if crashed
  timer.every(SAFETY_TIMING, send_ultrasonic_measure);  // Why 2nd timer in does not works ...
  timer.every(HANDLE_CMD_TIMING, handle_cmd);           // Check every 10 ms if new command to handle
    
  motor1.stop();                                // Disable motor 
  motor2.stop();                                // Disable motor
}

void loop() {
  timer.tick();                                 // tick the timer
}
