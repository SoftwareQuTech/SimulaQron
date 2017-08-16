CC=gcc
CFLAGS=-I.
DEPS = cqc.h
OBJ = cqc.o test.o
SEND = cqc.o testSend.o
RECV = cqc.o testRecv.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

test: $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

send: $(SEND)
	gcc -o $@ $^ $(CFLAGS)

recv: $(RECV)
	gcc -o $@ $^ $(CFLAGS)
