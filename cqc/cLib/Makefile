CC=gcc
CFLAGS=-I. -Wall
DEPS = cqc.h
MAIN = test.o
OBJ = cqc.o test_cqc.o
TEST_OBJ = testGates.o
TEST_FILES = testGates.c
SEND = cqc.o testSend.o
RECV = cqc.o testRecv.o
.PHONY: clean tests all
.DEFAULT: all

all: test send recv tests

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

test: $(OBJ) $(MAIN)
	gcc -o $@ $^ $(CFLAGS)

send: $(SEND)
	gcc -o $@ $^ $(CFLAGS)

recv: $(RECV)
	gcc -o $@ $^ $(CFLAGS)

tests: $(TESTS)
	$(CC) -c -o $(TEST_OBJ) $(TEST_FILES) $(CFLAGS)
	$(CC) -o testGates testGates.o $(OBJ) $(CFLAGS)

clean:
	rm -f $(MAIN) $(OBJ) $(TEST_OBJ) $(SEND) $(RECV) test send recv
