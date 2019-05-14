BIN = train

CFLAGS = -std=c99 -Wall -Wextra -pedantic -Ofast -flto -march=native

LDFLAGS = -lm

CC = gcc

SRC = train.c Tinn.c

all:
	$(CC) -o $(BIN) $(SRC) $(CFLAGS) $(LDFLAGS)

run:
	./$(BIN)

clean:
	rm -f $(BIN)%