// Original: https://github.com/openai/gym/blob/master/gym/envs/classic_control/cartpole.py

float gravity     = 9.8;
float masscart    = 1.0;
float masspole    = 0.1;
float total_mass  = (masspole + masscart);
float pole_length = 0.5; // actually half the pole's length
float polemass_length = (masspole * pole_length);
float force_mag   = 10.0;
float tau         = 0.02;  // seconds between state updates

float theta_threshold_radians = 12 * 2 * PI / 360;
float x_threshold = 2.4;

float x;
float x_dot;
float theta;
float theta_dot;

void reset() {
  x         = float(random(-500, +500) / 10000.0);
  x_dot     = float(random(-500, +500) / 10000.0);
  theta     = float(random(-500, +500) / 10000.0);
  theta_dot = float(random(-500, +500) / 10000.0);
}

float step(bool action) {
  float force = force_mag ? action : -force_mag;
  float costheta = cos(theta);
  float sintheta = sin(theta);
  
  float temp = (force + polemass_length * theta_dot * theta_dot * sintheta) / total_mass;
  float thetaacc = (gravity * sintheta - costheta * temp) / (pole_length * (4.0/3.0 - masspole * costheta * costheta / total_mass));
  float xacc = temp - polemass_length * thetaacc * costheta / total_mass;
  
  x = x + tau * x_dot;
  x_dot = x_dot + tau * xacc;
  theta = theta + tau * theta_dot;
  theta_dot = theta_dot + tau * thetaacc;

  bool done = (x < -x_threshold)
           || (x > x_threshold)
           || (theta < -theta_threshold_radians)
           || (theta > theta_threshold_radians);

  if(done)
    return 0.0;
  return 1.0;
}

void setup() {
  reset();
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    int _read = Serial.parseInt();
    if(_read == 2) {
      Serial.println("Reset");
      reset();
      Serial.flush();
    } else {
      bool cmd = (bool)_read;
      float reward = step(cmd);
      bool  done   = reward == 0.0 ? true : false;
      Serial.flush();
      Serial.print(x);
      Serial.print(",");
      Serial.print(x_dot);
      Serial.print(",");
      Serial.print(theta);
      Serial.print(",");
      Serial.print(theta_dot);
      Serial.print(",");
      Serial.print(reward); 
      Serial.print(",");
      Serial.println(done);
      if(done) reset();
    }
  }
}
