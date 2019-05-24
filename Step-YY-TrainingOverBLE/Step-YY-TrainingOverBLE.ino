#define MINIMUM 100
#define MAXIMUM 900
#define SAFE    100

int  target;
int  distance;
int  score;
bool done;

void new_game() {
  target = random(MINIMUM+SAFE, MAXIMUM-SAFE);
}

void perform_action(int cursor) {
  done = false;
  distance = target - cursor;
  score = 0;
  // Check if we are outside of range
  if((cursor < MINIMUM) || (cursor > MAXIMUM)) {
    done = true;
    score = - 100;
  // Check if we are on the target
  } else if (cursor == target) {
    done = true;
    score = 1000;
  // If not dead nor on the spot we compute the score
  } else {
    score = 800 - abs(distance);
  }
}

void setup() {
  randomSeed(analogRead(0)+millis());
  new_game();
  Serial.begin(115200);
  Serial.println("Ready to play");
}

void loop() {
  if (Serial.available() > 0) {      
    int cursor = Serial.parseInt();
    perform_action(cursor);
    Serial.print(distance);
    Serial.print(",");
    Serial.print(score);
    Serial.print(",");
    Serial.println(done);
    if(done) new_game();
  }
}
