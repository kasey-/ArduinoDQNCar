#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "genann.h"

int main(int argc, char *argv[])
{
    printf("GENANN load model from Keras.\n");

    /* Input data for the XOR function. */
    const double in[6][5] = {
        {0.0, 0.0, 0.0, 0.0, 0.0},
        {1.0, 0.0, 0.0, 0.0, 0.0},
        {0.0, 1.0, 0.0, 0.0, 0.0},
        {0.0, 0.0, 1.0, 0.0, 0.0},
        {0.0, 0.0, 0.0, 1.0, 0.0},
        {0.0, 0.0, 0.0, 0.0, 1.0},
    };

    const double tg[6][3] = {
        {0.0, 0.0, 1.0},
        {0.0, 0.0, 1.0},
        {0.0, 1.0, 0.0},
        {1.0, 0.0, 0.0},
        {0.0, 0.0, 1.0},
    };

    //genann *ann = genann_init(5, 2, 8, 3);

    /* Train on the four labeled data points many times. 
    double lr = 0.5;
    double lr_decay = 0.9999;
    double lr_min   = 0.001;
    for (int i = 0; i < 70000; ++i) {
        for (int j = 0; j < 6; j++)
            genann_train(ann, in[j], tg[j], lr);
        if(lr > lr_min)
            lr = lr*lr_decay;
        if(i % 1000 == 0.0)
            printf("%f\n",lr);
    }*/

    /* Load model. 
    FILE* const file = fopen("./keras.model", "w");
    genann_write(ann, file);
    fclose(file); */

    /* Load model. */
    FILE* const file = fopen("./keras.model", "r");
    genann *ann = genann_read(file);
    fclose(file); 

    /* Run the network and see what it predicts. */
    for(int i = 0; i < 6; i++) {
        const double *r = genann_run(ann, in[i]);
        printf("Output %d is [%1.2f, %1.2f, %1.2f]\n", i, r[0], r[1], r[2]);
    }

    genann_free(ann);
    return 0;
}