#include "Tinn.h"
#include <stdio.h>

#define NN_INPUT    7
#define NN_HIDDEN   8
#define NN_OUTPUT   2
#define NN_SAMPLES  1500

int main() {
    /* Init training dataset */
    float in[NN_SAMPLES][NN_INPUT];
    float tg[NN_SAMPLES][NN_OUTPUT];

    FILE* const file = fopen("train.txt", "r");
    for(int i = 0; i < NN_SAMPLES; i++)
        fscanf(file, "%f %f %f %f %f %f %f %f %f\n",  &in[i][0], &in[i][1], &in[i][2], &in[i][3], &in[i][4], &in[i][5], &in[i][6], &tg[i][0], &tg[i][1]);
    fclose(file);

    Tinn tinn = xtbuild(NN_INPUT, NN_HIDDEN, NN_OUTPUT);

    /* Train */
    float err = 0.0;
    float lr  = 0.2;
    for(int i = 0; i < 25000; i++) {
        for(int j = 0; j < NN_SAMPLES; j++) {
            err += xttrain(tinn, in[j], tg[j], lr) / NN_SAMPLES;
        }
        //printf("Error   : %f\n",err);
        //printf("Learn R : %f\n",lr);
        lr = lr * 0.99999;
        err = 0.0;
    }

    /* Display biases */
    printf("Biases  : ");
    for (int i = 0; i < tinn.nb; i++)
        printf("%f, ", tinn.b[i]);
    printf("\n");

    /* Display weights */
    printf("Weights : ");
    for (int i = 0; i < tinn.nw; i++)
        printf("%f, ", tinn.w[i]);
    printf("\n");

    /* Display result */
    float *output = xtpredict(tinn,in[0]);
    printf("Output  : %f %f\n",output[0],output[1]);

    return 0;
}
