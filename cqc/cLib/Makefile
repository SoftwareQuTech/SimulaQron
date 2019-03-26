CC=gcc
CFLAGS=-I. -Wall -std=c11
DEPS = cqc.h
CORE = cqc.o

.PHONY: clean tests all
.DEFAULT: all

all: qubit send recv gates

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

qubit: $(CORE) testQubit.o
	$(CC) -o $@ $^ $(CFLAGS)

send: $(CORE) testSend.o
	$(CC) -o $@ $^ $(CFLAGS)

recv: $(CORE) testRecv.o
	$(CC) -o $@ $^ $(CFLAGS)

gates: $(CORE) test_cqc.o testGates.o
	$(CC) -o $@ $^ $(CFLAGS) -lm

clean:
	rm -f *.o qubit send recv gates
