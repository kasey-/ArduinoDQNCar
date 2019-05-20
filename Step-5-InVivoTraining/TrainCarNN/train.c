#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "genann.h"

int main(int argc, char *argv[])
{
    printf("GENANN example 1.\n");
    printf("Train a small ANN to the XOR function using backpropagation.\n");

    /* This will make the neural network initialize differently each run. */
    /* If you don't get a good result, try again for a different result. */
    srand(time(0));

    /* Input and expected out data for the XOR function. */
    const double in[20][6] = {
        /* Normal drive */
        { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 },
        { 1.0, 0.0, 0.0, 0.0, 0.0, 0.0 },
        { 0.0, 1.0, 0.0, 0.0, 0.0, 0.0 },
        { 0.0, 0.0, 1.0, 0.0, 0.0, 0.0 },
        { 0.0, 0.0, 0.0, 1.0, 0.0, 0.0 },

        /* Sensor stop */
        { 0.0, 0.0, 0.0, 0.0, 1.0, 0.0 },
        { 1.0, 0.0, 0.0, 0.0, 1.0, 0.0 },
        { 0.0, 1.0, 0.0, 0.0, 1.0, 0.0 },
        { 0.0, 0.0, 1.0, 0.0, 1.0, 0.0 },
        { 0.0, 0.0, 0.0, 1.0, 1.0, 0.0 },

        { 0.0, 0.0, 0.0, 0.0, 0.0, 1.0 },
        { 1.0, 0.0, 0.0, 0.0, 0.0, 1.0 },
        { 0.0, 1.0, 0.0, 0.0, 0.0, 1.0 },
        { 0.0, 0.0, 1.0, 0.0, 0.0, 1.0 },
        { 0.0, 0.0, 0.0, 1.0, 0.0, 1.0 },

        { 0.0, 0.0, 0.0, 0.0, 1.0, 1.0 },
        { 1.0, 0.0, 0.0, 0.0, 1.0, 1.0 },
        { 0.0, 1.0, 0.0, 0.0, 1.0, 1.0 },
        { 0.0, 0.0, 1.0, 0.0, 1.0, 1.0 },
        { 0.0, 0.0, 0.0, 1.0, 1.0, 1.0 }
     };

    const double tg[20][2] = {
        { 0.5, 0.5 },
        { 1.0, 1.0 },
        { 0.5, 1.0 },
        { 0.0, 0.0 },
        { 1.0, 0.5 },
        
        { 0.5, 0.5 },
        { 0.5, 0.5 },
        { 0.5, 0.5 },
        { 0.0, 0.0 },
        { 0.5, 0.5 },
        
        { 0.5, 0.5 },
        { 0.5, 0.5 },
        { 0.5, 0.5 },
        { 0.0, 0.0 },
        { 0.5, 0.5 },

        { 0.5, 0.5 },
        { 0.5, 0.5 },
        { 0.5, 0.5 },
        { 0.0, 0.0 },
        { 0.5, 0.5 }
    };

    /* New network with 6 inputs, 2 hidden layer of 16 neurons, and 2 output. */
    genann *ann = genann_init(6, 2, 8, 2);

    /* Train on the four labeled data points many times. */
    double lr = 0.5;
    double lr_decay = 0.9999;
    double lr_min   = 0.001;
    for (int i = 0; i < 70000; ++i) {
        for (int j = 0; j < 20; j++)
            genann_train(ann, in[j], tg[j], lr);
        if(lr > lr_min)
            lr = lr*lr_decay;
        if(i % 1000 == 0.0)
            printf("%f\n",lr);
    }

    /* Run the network and see what it predicts. */
    for(int i = 0; i < 6; i++)
        printf("Output for %d is [%1.2f, %1.2f]\n", i, genann_run(ann, in[i])[0], genann_run(ann, in[i])[1]);
    
    /* save weights */
    FILE* const file = fopen("./CarNN-6-2-8-2.model", "w");
    genann_write(ann, file);
    fclose(file);

    genann_free(ann);
    return 0;
}