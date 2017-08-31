CC=gcc
CFLAGS=-I.
DEPS = cqc.h
MAIN = test.o
OBJ = cqc.o test_cqc.o 
TEST_OBJ = testGates.o
TEST_FILES = testGates.c
SEND = cqc.o testSend.o
RECV = cqc.o testRecv.o

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

