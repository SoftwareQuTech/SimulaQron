#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <math.h>
#include <sys/types.h>
#include <sys/socket.h>

// #include <stdlib.h>

#include <netinet/in.h>
#include <netdb.h>

#include <string.h>

#include "cqc.h"

/*****
 Functions purely used for testing purposes
******/

/*
 *  cqc_tomography_dir
 *
 *  Obtain tomographic data for a prepared qubit, for testing purposes.
 *
 *  Arguments:
 *  func	function to call to prepare qubit for tomography
 *  iter	iterations to perform
 *  dir		direction to measure (0=Z, 1=X, 2=Y)
 *
 *  Returns average (in [-1,1] interval), or -10 for failure.
 */

float
cqc_tomography_dir(cqc_lib *cqc, uint16_t (*func)(cqc_lib *), uint32_t iter, uint8_t dir)
{
	int i;
	int outcome;
	int count;
	float iterf;
	uint8_t cmd;
	float ratio;
	uint16_t qubit;

	/* Translate the direction into a rotation command */
	switch(dir) {
		case 1:
			cmd = CQC_CMD_H;
			break;
		case 2:
			cmd = CQC_CMD_K;
			break;
	}
	
	/* Measure in the given direction iter times to gather stats */	
	count = 0;
	for(i = 0; i < iter; i++) {

		/* Prepare the qubit */
		qubit = (* func)(cqc);
		if(qubit < 0) {
			fprintf(stderr,"Failed to prepare qubit for tomography.\n");
			return(-10);
		}

		/* Measure in the indicated direction */
		if (dir > 0) {
			if (cqc_simple_cmd(cqc, cmd, qubit, 1) < 0) {
				fprintf(stderr,"Unable to measure in the indicated basis.\n");
				return(-10);
			}
			cqc_wait_until_done(cqc, 1);
		}

		outcome = cqc_measure(cqc, qubit);
		if (outcome < 0) {
			fprintf(stderr,"Tomography measurement failed for qubit %u.\n",qubit);
			return(-10);
		}

		/* Add to the total count: note outcome needs to be +/-1 for 0/1 to yield expectations */
		if (outcome == 0) {
			count++;
		} else {
			count--;
		}
	}

	ratio = ((float)count)/((float) iter);
	return(ratio);

}

/* 
 * cqc_test_qubit
 * 
 * Prepares a qubit according to the indicated function, then performs tomography to verify the preparation up to the indicated precision.
 *
 * Arguments
 * cqc		cqc connection
 * func		function to invoke to prepare qubit 
 * iter		number of times to iterate the test in tomography
 * epsilon	desired precision
 * exp_x	expected value for <X>
 * exp_y	expted value for <Y>
 * exp_z	expected value for <Z>
 *
 * Returns
 * 1  for success - state lies in desired interval
 * 0  for no functional failure but state does not lie in desired interval
 * -1 functional error
 */

int
cqc_test_qubit(cqc_lib *cqc, uint16_t (*func)(cqc_lib *), uint32_t iter, float epsilon, float exp_x, float exp_y, float exp_z)
{
	int ret;
	float tomo_x, tomo_z, tomo_y;
	float diff_x, diff_y, diff_z;
	
	/* Run tomography in X, Z and Y directions */
	tomo_z = cqc_tomography_dir(cqc, func, iter, 0);
	tomo_x = cqc_tomography_dir(cqc, func, iter, 1);
	tomo_y = cqc_tomography_dir(cqc, func, iter, 2);
	if ((tomo_x <= -10) || (tomo_z <= -10) || (tomo_y <= -10)) {
		fprintf(stderr,"Tomography failed.\n");
		return(-1);
	}

	/* Compare to the expected results up to the desired precision */
	diff_x = fabsf(tomo_x - exp_x);
	diff_y = fabsf(tomo_y - exp_y);
	diff_z = fabsf(tomo_z - exp_z);

	ret = 1;
	if (diff_x > epsilon) {
		printf("X target not met, got %f expected %f\n", tomo_x, exp_x);
		ret = 0;
	}
	if (diff_z > epsilon) {
		printf("Z target not met, got %f expected %f\n", tomo_z, exp_z);
		ret = 0;
	}
	if (diff_y > epsilon) {
		printf("Y target not met, got %f expected %f\n", tomo_y, exp_y);
		ret = 0;
	}

	return(ret);

}

