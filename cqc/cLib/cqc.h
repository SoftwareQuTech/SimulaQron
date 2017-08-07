
#ifndef CQC_H
#define CQC_H


/* Basic CQC Header format */
#define CQC_HDR_LENGTH 		8
typedef struct
{
	uint8_t version; /* Pretty wasteful to use a char for that. 3 bits would be plenty, but only done for python now as the total must be 4 bytes */
	uint8_t type;		/* Packet control type */
	uint16_t app_id; 	/* Application ID */
	uint32_t cmdLength;	/* Total length of command instructions to send */
	void *payload; 		/* Pointer to cmd payload */
} __attribute__((__packed__)) cqcHeader;

/* CQC Version */
#define CQC_VERSION 		0

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

/*
	Definitions for the command header and commands.
*/

#define	CQC_CMD_HDR_LENGTH      4
typedef struct
{
	uint16_t qubit_id;	/* Qubit to perform the operation on */
	uint8_t instr;		/* Instruction to execute */
	uint8_t options;	/* Options when executing the command */
	void *extraCmd;		/* Additional details for this command */
} __attribute__((__packed__)) cmdHeader;

/* Possible commands */
#define CQC_CMD_I		0	/* Identity (do nothing, wait one step) */
#define	CQC_CMD_NEW		1	/* Ask for a new qubit */
#define CQC_CMD_MEASURE		2	/* Measure qubit */
#define CQC_CMD_RESET		3	/* Reset qubit to |0> */
#define CQC_CMD_SEND		4	/* Send qubit to another node */
#define CQC_CMD_RECV		5	/* Ask to receive qubit */
#define CQC_CMD_EPR		6	/* Create EPR pair with the specified node */

#define CQC_CMD_X		10	/* Pauli X */
#define CQC_CMD_Z		11	/* Pauli Z */
#define CQC_CMD_Y		12	/* Pauli Y */
#define CQC_CMD_T		13	/* T Gate */

#define CQC_CMD_CNOT		20	/* CNOT Gate with this as control */
#define CQC_CPHASE		21	/* CPHASE Gate with this as control */

/* Command options */
#define CQC_OPT_NOTIFY		0x01	/* Send a notification when cmd done */
#define CQC_OPT_ACTION		0x02	/* On if there are actions to execute when done */
#define CQC_OPT_BLOCK		0x03	/* Block until command is done */

/* Additional cmd details (optional) */
#define CQC_CMD_XTRA_HDR	24
typedef struct
{
	uint8_t xtra_qubit_id;	/* ID of the additional qubit */
	uint8_t angle_step;	/* Angle step of rotation */
	uint16_t remote_app_id;	/* Remote application ID */
	uint64_t remote_node;	/* IP of the remote node */
	uint32_t cmdLength;	/* Length of the cmds to exectute upon completion */
	void *cmdPayload;	/* Details to execute when done with this command */
} __attribute__((__packed__)) cmdHeader;

#endif

