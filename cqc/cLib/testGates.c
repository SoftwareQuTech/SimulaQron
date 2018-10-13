#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>

// #include <stdlib.h>

#include <netinet/in.h>
#include <netdb.h>

#include <string.h>
#include<arpa/inet.h>

#include "cqc.h"


/*
 * make_plus
 *
 * Prepares a plus state
 *
 */
uint16_t
make_plus(cqc_lib *cqc)
{
	uint16_t qubit;

	/* Create a new qubit in |0> */
	if (cqc_simple_cmd(cqc, CQC_CMD_NEW, 0 ,0) < 0) {
		fprintf(stderr,"Qubit creation failed.\n");
		return(-1);
	}
	qubit = cqc_wait_until_newok(cqc);
	if(qubit < 0) {
		fprintf(stderr,"ERROR: Test failed.\n");
		return(-1);
	}

	/* Turn it into |+> */
	if (cqc_simple_cmd(cqc, CQC_CMD_H, qubit,1) < 0) {
		fprintf(stderr,"Cannot apply gate.\n");
		return(-1);
	}
	if(cqc_wait_until_done(cqc, 1) < 0) {
		fprintf(stderr,"ERROR: Test failed.\n");
		return(-1);
	}

	return(qubit);
}


/*
 * make_zero
 *
 * Prepares a plus state
 *
 */
uint16_t
make_zero(cqc_lib *cqc)
{
	uint16_t qubit;

	/* Create a new qubit in |0> */
	if (cqc_simple_cmd(cqc, CQC_CMD_NEW, 0, 0) < 0) {
		fprintf(stderr,"Qubit creation failed.\n");
		return(-1);
	}
	qubit = cqc_wait_until_newok(cqc);
	if(qubit < 0) {
		fprintf(stderr,"ERROR: Test failed.\n");
		return(-1);
	}

	/* Turn it into |+> */
	if (cqc_simple_cmd(cqc, CQC_CMD_I, qubit,1) < 0) {
		fprintf(stderr,"Cannot apply gate.\n");
		return(-1);
	}
	if(cqc_wait_until_done(cqc, 1) < 0) {
		fprintf(stderr,"ERROR: Test failed.\n");
		return(-1);
	}

	return(qubit);
}


/*
 * make_k
 *
 * Prepares a y eigenstate
 *
 */
uint16_t
make_k(cqc_lib *cqc)
{
	uint16_t qubit;

	/* Create a new qubit in |0> */
	if (cqc_simple_cmd(cqc, CQC_CMD_NEW, 0, 0) < 0) {
		fprintf(stderr,"Qubit creation failed.\n");
		return(-1);
	}
	qubit = cqc_wait_until_newok(cqc);
	if(qubit < 0) {
		fprintf(stderr,"ERROR: Test failed.\n");
		return(-1);
	}

	/* Turn it into |+> */
	if (cqc_simple_cmd(cqc, CQC_CMD_K, qubit,1) < 0) {
		fprintf(stderr,"Cannot apply gate.\n");
		return(-1);
	}
	if(cqc_wait_until_done(cqc, 1) < 0) {
		fprintf(stderr,"ERROR: Test failed.\n");
		return(-1);
	}

	return(qubit);
}


int main(int argc, char *argv[]) {

	uint16_t portno;
	char *hostname;
	cqc_lib *cqc;
	int app_id;
	int outcome;

	/* Retrieve arguments from command line */
   	if (argc < 3) {
      		fprintf(stderr,"usage %s hostname port \n", argv[0]);
      		exit(0);
   	}
	hostname = argv[1];
   	portno = atoi(argv[2]);

	/* In this example, we are simply application 10 */
	app_id = 10;

	/* In this example, we will not check for errors. All functions return -1 on failure */
	cqc = cqc_init(app_id);
	cqc_connect(cqc, hostname, portno);

	/* Test whether we can make the zero state */
	outcome = cqc_test_qubit(cqc, make_zero, 500, 0.1, 0, 0, 1);
	if (outcome < 0) {
		fprintf(stderr,"Test failed.\n");
		exit(0);
	}
	printf("Testing |0> preparation......................");
	if (outcome == 0) {
		printf("fail\n");
	} else {
		printf("ok\n");
	}

	/* Test whether we can make the plus state */
	outcome = cqc_test_qubit(cqc, make_plus, 500, 0.1, 1, 0, 0);
	if (outcome < 0) {
		fprintf(stderr,"Test failed.\n");
		exit(0);
	}
	printf("Testing |+> preparation......................");
	if (outcome == 0) {
		printf("fail\n");
	} else {
		printf("ok\n");
	}

	/* Test whether we can make the y 0 eigenstate */
	outcome = cqc_test_qubit(cqc, make_k, 500, 0.1, 0, 1, 0);
	if (outcome < 0) {
		fprintf(stderr,"Test failed.\n");
		exit(0);
	}
	printf("Testing |1> preparation......................");
	if (outcome == 0) {
		printf("fail\n");
	} else {
		printf("ok\n");
	}

   	return 0;
}
