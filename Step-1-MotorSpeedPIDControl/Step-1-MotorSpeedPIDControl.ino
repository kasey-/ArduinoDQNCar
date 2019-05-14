#include <EnableInterrupt.h>      // used to attach interrupts on sensor pin
#include <timer.h>                // used to time PID and debug
#include <L298N.h>                // used to drive motor
#include <PID_v1.h>               // used to compute PID

#define KP  2.0                   // P = 2.0  
#define KI  1.0                   // I = 1.0
#define KD  0.01                  // D = 0.01 
#define KF  0.9                   // Average over 10 samples

#define SPEEDSENSOR_PIN    A3     // Sensor read pin
#define SENSOR_HOLES       20.0   // Number of holes in encoder
#define WHEEL_DIAM         67.0   // Diameter of the wheel

#define PID_SAMPLING_RATE  50

// Right Motor
#define ENA 5
#define IN1 6
#define IN2 7

#define MOTOR_SPEED_MIN_PWM  70   // minimal PWM to drive motor
#define MOTOR_SPEED_MAX_PWM 255   // maximal PWM to drive motor = max arduino PWM
#define MOTOR_SPEED_MIN_MMS 280.0 // speed mm/s for 80 PWM with full batteries
#define MOTOR_SPEED_MAX_MMS 740.0 // speed mm/s for max PWM with full batteries

double   speed_measured = 0.0;    // variable to store speed measured from sensor
double   speed_target   = 2 * WHEEL_DIAM * PI; // test target = 2 rotation / s => 420.97 mm/s
double   speed_output   = 0.0;    // the output from the PID in mm/s
int      pwm_output     = 0;      // the converted output from the PID in PWM
uint32_t last_int_time  = 0;      // variable used to compute the difference in measure and deduct speed

L298N motor(ENA, IN1, IN2);       // motor instance
PID pid(&speed_measured, &speed_output, &speed_target,KP,KI,KD,P_ON_M, DIRECT); // pid instance

Timer<2> timer;                   // two timer, one debug print, one compute PID

int map_speed(double x, double in_min, double in_max, int out_min, int out_max) {
  // special mapping feature taking double in input (mm/s) and casting to int (PWM)
  int out = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
  return out;
}

bool debug_speed(void *) {            // every 50 ms
  Serial.print(speed_measured,DEC);   // speed measured from the sensor
  Serial.print("\t");
  Serial.print(speed_target,DEC);     // speed target 2 rotation / s => 420.97 mm/s
  Serial.print("\t");
  Serial.print(speed_output,DEC);     // PID output 
  Serial.print("\t");
  Serial.println(pwm_output);         // PWM output from the PID
  return true;
}

bool drive_motor(void *) {            // every 50 ms
  pid.Compute();                      // compute PID
                                      // map the PWM output based on PID output speed
  pwm_output = map_speed(speed_output,
    MOTOR_SPEED_MIN_MMS, MOTOR_SPEED_MAX_MMS,
    MOTOR_SPEED_MIN_PWM, MOTOR_SPEED_MAX_PWM);

  motor.setSpeed(pwm_output);         // set motor output as mapped speed output
  motor.forward();                    // re-enable motor driver 
  
  return true;
}

double compute_speed(float delta_int) {
  /*
   * Wheel perimeter (mm) = Wheel Diameter (mm) * PI
   * Distance over one hole (mm) = Wheel perimeter (mm) / Number sensor hole
   * Time since last hole passed (s) = (Cycles Now (us) - Cycles last hole (us)) / 1 000 000
   * Speed (mm/s) = Distance over one hole (mm) / time since last hole passed (s)
   */
  return (WHEEL_DIAM * PI / SENSOR_HOLES) / (delta_int / 1000000.0);
}

void isr_speed_measure() {
  float delta_int = micros() - last_int_time; // Time since last hole passed in us
  speed_measured = speed_measured * KF + compute_speed(delta_int) * (1.0 - KF);  // Compute speed using delta + average over 10 samples
  last_int_time = micros();                   // Buffer storing previous hole observqtion
}

void setup() {
  Serial.begin(115200);                       // Start serial 115200
  
  motor.setSpeed(0);                          // Speed zero for safe start
  
  pid.SetMode(AUTOMATIC);                     // PID Automatic to enable it
  pid.SetSampleTime(PID_SAMPLING_RATE);       // Sampling time 50ms like timer
  pid.SetOutputLimits(MOTOR_SPEED_MIN_MMS, MOTOR_SPEED_MAX_MMS); // Define PID clipping to min and max motor PWM speed

  timer.every(PID_SAMPLING_RATE, debug_speed); // Start debug speed timer every 50 ms
  timer.every(PID_SAMPLING_RATE, drive_motor); // Start update motor driving every 50 ms
  
  pinMode(SPEEDSENSOR_PIN, INPUT);            // Setup sensor reading pin as an input
  enableInterrupt(SPEEDSENSOR_PIN, isr_speed_measure, RISING);  // Attach rising interupt (only available) to isr_speed_measure
  last_int_time = micros();                   // Init the speed buffer
}

void loop() {
  timer.tick();                               // make tick the timer
}
