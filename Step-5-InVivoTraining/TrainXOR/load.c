#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "genann.h"

int main(int argc, char *argv[])
{
    printf("GENANN load model.\n");
    printf("Load a small ANN to the XOR function using backpropagation.\n");

    /* Input data for the XOR function. */
    const double input[4][2] = {{0, 0}, {0, 1}, {1, 0}, {1, 1}};

    /* Load model. */
    FILE* const file = fopen("./xor.model", "r");
    genann *ann = genann_read(file);
    fclose(file); 

    /* Run the network and see what it predicts. */
    printf("Output for [%1.f, %1.f] is %1.2f.\n", input[0][0], input[0][1], *genann_run(ann, input[0]));
    printf("Output for [%1.f, %1.f] is %1.2f.\n", input[1][0], input[1][1], *genann_run(ann, input[1]));
    printf("Output for [%1.f, %1.f] is %1.2f.\n", input[2][0], input[2][1], *genann_run(ann, input[2]));
    printf("Output for [%1.f, %1.f] is %1.2f.\n", input[3][0], input[3][1], *genann_run(ann, input[3]));

    genann_free(ann);
    return 0;
}