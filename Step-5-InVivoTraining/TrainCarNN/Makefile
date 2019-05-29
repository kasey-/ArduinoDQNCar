CFLAGS = -Wall -Wshadow -O3 -g -march=native
LDLIBS = -lm

all: check 

sigmoid: CFLAGS += -Dgenann_act=genann_act_sigmoid_cached
sigmoid: all

threshold: CFLAGS += -Dgenann_act=genann_act_threshold
threshold: all

linear: CFLAGS += -Dgenann_act=genann_act_linear
linear: all

train: train.o genann.o

load: load.o genann.o

clean:
	$(RM) *.o
	$(RM) train load *.exe

.PHONY: sigmoid threshold linear clean
