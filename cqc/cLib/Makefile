CC=gcc
CFLAGS=-I.
DEPS = cqc.h
OBJ = cqc.o test.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

test: $(OBJ)
	gcc -o $@ $^ $(CFLAGS)
