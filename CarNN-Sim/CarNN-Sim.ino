extern "C"{
  #include "Tinn.h"
};
#include "ServoEasing.h"
#include <L298N.h>

// Servo
#define SERVO_PIN           11
#define SERVO_OFFSET        1
#define SERVO_SCAN_RANGE    80
#define SERVO_SCAN_STEP     10
#define SERVO_DELAY         300

// Ultrasonic Sensor
#define UTRASONIC_TRIG_PIN  A0
#define UTRASONIC_ECHO_PIN  A1
#define UTRASONIC_TIMEOUT   3000
#define UTRASONIC_SOUND_C   58.273

// Car state
#define CAR_STATE_FORWARD  0
#define CAR_STATE_RIGHT    1
#define CAR_STATE_BACKWARD 2
#define CAR_STATE_LEFT     3
#define CAR_STATE_STOP    -1

// Sensor setup
#define DIST_SENS_RIGHT_PIN A4
#define DIST_SENS_LEFT_PIN  A5
#define USER_BUTTON_PIN     13

// Motor Right
#define ENA 5
#define IN1 6
#define IN2 7
// Motor Left
#define IN3 8
#define IN4 9
#define ENB 10
// Motor Settings
#define MOTOR_SPEED 180

// IR Remote Hexa Keycode
#define KEYCODE_UP    0x00FD8877
#define KEYCODE_RIGHT 0x00FD6897
#define KEYCODE_LEFT  0x00FD28D7
#define KEYCODE_DOWN  0x00FD9867
#define KEYCODE_HOLD  0xFFFFFFFF

// Neural Network Parameters, Biases & Weights
#define NN_INPUT  7
#define NN_HIDDEN 8
#define NN_OUTPUT 2
float biases[] = {
  -0.222918, 0.413817
};

float weights[] = {
  -12.501347, -11.793865, 0.001139, -0.992627, -5.504624, 2.266316, 9.043344,
  -5.276033, -5.826567, 0.819411, -0.175151, 0.550130, -3.078978, -0.824877,
  -5.043294, -11.007901, 12.547348, -1.240129, -15.197927, -6.990236, 4.029067,
  8.498116, 8.446489, 4.486276, 3.119950, -9.409198, -2.654408, 8.194310,
  -5.346487, -5.685745, -10.114454, 12.267869, -2.646714, -9.131749, 1.831171,
  -5.059334, -5.897607, -5.345176, -3.033247, 1.703548, -5.161853, 10.309111,
  -3.485375, -5.364698, -11.368389, 7.033315, -5.917485, -8.546207, 10.566115,
  7.061646, 7.393685, 3.445619, 1.745158, -6.840068, 1.082639, -0.313161,
  3.004426, 9.876628, -1.489108, -2.399122, 6.871397, -0.177590, -5.519954,
  1.983934, 3.181573, 5.098681, -2.461641, -3.174820, 2.713842, 2.086759,
  -3.970816, 2.758887
};

Tinn tinn ;

L298N motor1(ENA, IN1, IN2);
L298N motor2(ENB, IN3, IN4);

ServoEasing SensorServo;
int servoPositions[]     = {-80, -40, 0, 40, 80};
int servoCurrentPosition = 0;
int servoDirection       = 1;

float measure_ultrasonic_distance() {
  digitalWrite(UTRASONIC_TRIG_PIN, HIGH);  // set trig port high level for 10μs (at least 10μs)
  delayMicroseconds(10);
  digitalWrite(UTRASONIC_TRIG_PIN, LOW);   // set trig port low level
  float m1 = pulseIn(UTRASONIC_ECHO_PIN, HIGH, UTRASONIC_TIMEOUT);

  digitalWrite(UTRASONIC_TRIG_PIN, LOW);   // set trig port low level for 2μs
  delayMicroseconds(2);
  digitalWrite(UTRASONIC_TRIG_PIN, HIGH);  // set trig port high level for 10μs (at least 10μs)
  delayMicroseconds(10);
  digitalWrite(UTRASONIC_TRIG_PIN, LOW);   // set trig port low level
  float m2 = pulseIn(UTRASONIC_ECHO_PIN, HIGH, UTRASONIC_TIMEOUT);

  if(m1 > m2)
    return m1 / UTRASONIC_SOUND_C;
  else
    return m2 / UTRASONIC_SOUND_C;
}

void set_position_servo(int pos) {
  SensorServo.startEaseToD(pos + 90 + SERVO_OFFSET, SERVO_DELAY);
}

void drive_motor(float cmd_motor1, float cmd_motor2) {
  if(cmd_motor1 <= 0.25) {
    motor1.backward();
  } else if(cmd_motor1 > 0.25 && cmd_motor1 <= 0.75) {
    motor1.stop();
  } else {
    motor1.forward();
  }
  
  if(cmd_motor2 <= 0.25) {
    motor2.backward();
  } else if(cmd_motor2 > 0.25 && cmd_motor2 <= 0.75) {
    motor2.stop();
  } else {
    motor2.forward();
  }
}

float* predict_output() {
  float NN_input[7] = { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
    
  NN_input[0] = (float) !digitalRead(DIST_SENS_LEFT_PIN);
  NN_input[1] = (float) !digitalRead(DIST_SENS_RIGHT_PIN);

  return xtpredict(tinn,NN_input);
}

void setup() {
  Serial.begin(115200);
  
  pinMode(USER_BUTTON_PIN, INPUT_PULLUP);   // Set button as input and internal pull-up mode

  pinMode(UTRASONIC_ECHO_PIN, INPUT);       // Set Ultrasonic echo port as input
  pinMode(UTRASONIC_TRIG_PIN, OUTPUT);      // Set Ultrasonic trig port as input

  SensorServo.attach(SERVO_PIN);
  SensorServo.startEaseToD(servoPositions[0], 500);
  
  // Setup the sensors
  pinMode(DIST_SENS_RIGHT_PIN, INPUT);
  pinMode(DIST_SENS_LEFT_PIN, INPUT);

  // Setup the neural network
  tinn = xtbuild(NN_INPUT, NN_HIDDEN, NN_OUTPUT);
  for(int i=0; i < tinn.nb; i++)
    tinn.b[i] = biases[i];
  for(int i=0; i < tinn.nw; i++)
    tinn.w[i] = weights[i];
  
  // Setup the motors
  motor1.stop();
  motor2.stop();
  motor1.setSpeed(MOTOR_SPEED);
  motor2.setSpeed(MOTOR_SPEED);
}

void loop() {
  if(!SensorServo.isMoving()) {
    Serial.print(SensorServo.getCurrentAngle());
    Serial.print("\t");
    Serial.println(measure_ultrasonic_distance(),DEC);
    set_position_servo(servoPositions[servoCurrentPosition]);
    
    if(servoCurrentPosition == 0) servoDirection =  1;
    if(servoCurrentPosition == 8) servoDirection = -1;
    servoCurrentPosition = servoCurrentPosition + 1 * servoDirection ;
  }
}
