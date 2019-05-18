extern "C"{
  #include "genann.h"
};

float weights[] = {
  0.0371650690, 0.5043044945, 0.5042459250, -0.0108662151,
  0.0260638197, -0.3022353853, 0.9244956919, 1.9806044750,
  -0.0988540601, -1.0035981681, -2.1475397975, -0.4016071864,
  -4.4084124871, -8.9295373245, -8.9330303161
};

genann *ann;
   
void setup() {
  Serial.begin(115200);
  ann = genann_init(2, 2, 2, 1);
  
  for (int i = 0; i < ann->total_weights; i++)
    ann->weight[i] = weights[i];
}

void loop() {
  const double input0[2] = { 0.0, 0.0 };
  Serial.println(genann_run(ann, input0)[0], DEC);
  const double input1[2] = { 1.0, 0.0 };
  Serial.println(genann_run(ann, input1)[0], DEC);
  const double input2[2] = { 0.0, 1.0 };
  Serial.println(genann_run(ann, input2)[0], DEC);
  const double input3[2] = { 1.0, 1.0 };
  Serial.println(genann_run(ann, input3)[0], DEC);
  delay(10000);
}
