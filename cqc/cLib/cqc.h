
#ifndef CQC_H
#define CQC_H


/* Basic CQC Header format */

typedef struct
{
	uint8_t version; /* Pretty wasteful to use a char for that. 3 bits would be plenty, but only done for python now as the total must be 4 bytes */
	uint8_t type;
	uint16_t app_id;
} __attribute__((__packed__)) cqcHeader;

/* CQC Version */
#define CQC_VERSION 0

/* Possible CQC Types */

#define CQC_HELLO		0	/* Alive check */
#define CQC_COMMAND 		1	/* Execute a command list */
#define CQC_FACTORY		2 	/* Start executing command list repeatedly */
#define CQC_EXPIRE		3	/* Qubit has expired */
#define	CQC_DONE		4	/* Command execution done */
#define CQC_RECV		5	/* Recevied qubit */
#define CQC_EPR_OK		6	/* Created EPR pair */
#define	CQC_MEASOUT		7	/* Measurement outcome */

#define	CQC_ERR_GENERAL		20	/* General purpose error (no details */
#define	CQC_ERR_NOQUBIT		21	/* No more qubits available */
#define	CQC_ERR_UNSUPP		22	/* Command sequence not supported */
#define	CQC_ERR_TIMEOUT		23	/* Timeout */

#endif

