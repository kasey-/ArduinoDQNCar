#include <L298N.h>                   // https://github.com/AndreaLombardo/L298N

// Ultrasonic Settings
#define UTRASONIC_LEFT_TRIG_PIN     A2
#define UTRASONIC_LEFT_ECHO_PIN     A3
#define UTRASONIC_MIDDLE_TRIG_PIN   A0
#define UTRASONIC_MIDDLE_ECHO_PIN   A1
#define UTRASONIC_RIGHT_TRIG_PIN    A4
#define UTRASONIC_RIGHT_ECHO_PIN    A5
#define UTRASONIC_TIMEOUT           5700UL // Ultrasonic timeout 5700 = 1m

float ultrasonic_measures[3];

// Safety Settings
#define SAFETY_CMD_DELAY      1000   // Stop the car if we did not received a cmd since 1000 s
#define BACKWARD_DELAY        2000   // Move backward after collision 2 s

unsigned long last_cmd_time;

// Motor Settings
#define MOTOR_RIGHT_ENA   5
#define MOTOR_RIGHT_IN1   6
#define MOTOR_RIGHT_IN2   7
#define MOTOR_LEFT_IN3    8
#define MOTOR_LEFT_IN4    9
#define MOTOR_LEFT_ENB    10
#define MOTOR_SPEED       80

L298N motor_right(MOTOR_RIGHT_ENA, MOTOR_RIGHT_IN1, MOTOR_RIGHT_IN2);
L298N motor_left(MOTOR_LEFT_ENB,   MOTOR_LEFT_IN3,  MOTOR_LEFT_IN4);

// Ml Settings
#define PENALTY_TURN  -0.8
#define PENALTY_DIST  -0.7
#define PENALTY_CRASH -500.0
#define BONUS_MOVE    0.5
#define ANSWER_DELAY  250

bool car_is_crashed;

void car_turn_left() {
  motor_right.stop();                                // Stop Right Motor
  motor_left.setSpeed(MOTOR_SPEED);                  // Move Left Motor at medium speed
  motor_left.forward();                              // Enable Left motor
}

void car_turn_right() {
  motor_left.stop();                                 // Stop Left Motor
  motor_right.setSpeed(MOTOR_SPEED);                 // Move Right Motor at medium speed
  motor_right.forward();                             // Enable Right motor 
}

void car_go_forward() {
  motor_right.setSpeed(MOTOR_SPEED);                 // Move Right motor at medium speed
  motor_left.setSpeed(MOTOR_SPEED);                  // Move Left motor at medium speed
  motor_right.forward();                             // Enable Right motor 
  motor_left.forward();                              // Enable Left motor     
}

void car_go_backward() {
  motor_right.setSpeed(MOTOR_SPEED);                 // Move motors at medium speed
  motor_left.setSpeed(MOTOR_SPEED);
  motor_right.backward();                            // Move motors backward to go out of collision
  motor_left.backward();
}

void car_stop() {
  motor_right.stop();
  motor_left.stop();
}

void update_cmd_time() {
  last_cmd_time = millis();
}

void do_security_check() {
  do_ultrasonic_measures();

  if(
      ultrasonic_measures[0] <= 0.1 ||  /* /!\ Declare has constant after test */
      ultrasonic_measures[1] <= 0.1 ||
      ultrasonic_measures[2] <= 0.1
    ) {
    car_is_crashed = true;
    car_stop();
  }

  if(last_cmd_time + SAFETY_CMD_DELAY < millis()) {
    car_stop();
  }
}

void reset_car() {
  if(car_is_crashed) {
    car_go_backward();
    delay(BACKWARD_DELAY);        // Move for 2.5s
  }
  
  car_stop();                              
  car_is_crashed  = false;
  do_ultrasonic_measures();
  print_sensors();
  Serial.println("");
}

void print_sensors() {
  Serial.print(ultrasonic_measures[0],DEC);
  Serial.print(',');
  Serial.print(ultrasonic_measures[1],DEC);
  Serial.print(',');
  Serial.print(ultrasonic_measures[2],DEC);
}

float measure_ultrasonic_distance(int trig_pin, int echo_pin) {
  digitalWrite(trig_pin, LOW);   // set trig port low level for 2μs
  delayMicroseconds(2);
  digitalWrite(trig_pin, HIGH);  // set trig port high level for 10μs (at least 10μs)
  delayMicroseconds(10);
  digitalWrite(trig_pin, LOW);   // set trig port low level
  float echo_time = pulseIn(echo_pin, HIGH, UTRASONIC_TIMEOUT);
  return (echo_time == 0.0) ? 1.0 : (echo_time / UTRASONIC_TIMEOUT);
}

void do_ultrasonic_measures() {
  ultrasonic_measures[0] = measure_ultrasonic_distance(UTRASONIC_LEFT_TRIG_PIN, UTRASONIC_LEFT_ECHO_PIN);
  ultrasonic_measures[2] = measure_ultrasonic_distance(UTRASONIC_RIGHT_TRIG_PIN, UTRASONIC_RIGHT_ECHO_PIN);
  ultrasonic_measures[1] = measure_ultrasonic_distance(UTRASONIC_MIDDLE_TRIG_PIN, UTRASONIC_MIDDLE_ECHO_PIN);
}

void step(int action) {
  if(car_is_crashed) {
    print_sensors();
    Serial.print(",");
    Serial.println(PENALTY_CRASH,DEC);
    car_stop();
    return;  
  }
  
  float reward = 0.0 ;

  switch(action) {
    case 0: // Turn left
      reward = PENALTY_TURN;
      car_turn_left();
    break;
    case 1: // Turn Right
      reward = PENALTY_TURN;
      car_turn_right();
    break;
    case 2: // Forward
      reward = BONUS_MOVE;
      car_go_forward();
    break;
  }

  delay(ANSWER_DELAY);
  do_ultrasonic_measures();
  print_sensors();
  Serial.print(",");
  Serial.println(reward,DEC);
}

void handle_serial_cmd() {
  if (Serial.available() > 0) {
    update_cmd_time();
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
  }
}

void setup() {
  Serial.begin(115200);             // Start serial 115200
  Serial.setTimeout(10);            // Serial timeout = 10 ms otherwise Parseint wait 1s '-_-

  pinMode(UTRASONIC_LEFT_ECHO_PIN, INPUT);       // Set Ultrasonic echo port as input
  pinMode(UTRASONIC_LEFT_TRIG_PIN, OUTPUT);      // Set Ultrasonic trig port as input
  pinMode(UTRASONIC_MIDDLE_ECHO_PIN, INPUT);     // Set Ultrasonic echo port as input
  pinMode(UTRASONIC_MIDDLE_TRIG_PIN, OUTPUT);    // Set Ultrasonic trig port as input
  pinMode(UTRASONIC_RIGHT_ECHO_PIN, INPUT);      // Set Ultrasonic echo port as input
  pinMode(UTRASONIC_RIGHT_TRIG_PIN, OUTPUT);     // Set Ultrasonic trig port as input

  update_cmd_time();
  car_is_crashed = false;

  car_stop();
}

void loop() {
  do_security_check();
  handle_serial_cmd();
}
