/*
Copyright (c) 2017, Stephanie Wehner
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. All advertising materials mentioning features or use of this software
   must display the following acknowledgement:
   This product includes software developed by Stephanie Wehner, QuTech.
4. Neither the name of the QuTech organization nor the
   names of its contributors may be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#ifndef CQC_H
#define CQC_H

#include <stdint.h>

/* Basic CQC Header format */

#define CQC_HDR_LENGTH 		8
typedef struct
{
	uint8_t version;        /* CQC interface version  */
	uint8_t type;		/* Packet control type */
	uint16_t app_id; 	/* Application ID */
	uint32_t length;	/* Total length of command instructions to send */
} __attribute__((__packed__)) cqcHeader;

/* CQC Version */
#define CQC_VERSION 		2

/* Possible CQC Types */

#define CQC_TP_HELLO		0	/* Alive check */
#define CQC_TP_COMMAND 		1	/* Execute a command list */
#define CQC_TP_FACTORY		2 	/* Start executing command list repeatedly */
#define CQC_TP_EXPIRE		3	/* Qubit has expired */
#define	CQC_TP_DONE		4	/* Command execution done */
#define CQC_TP_RECV		5	/* Recevied qubit */
#define CQC_TP_EPR_OK		6	/* Created EPR pair */
#define	CQC_TP_MEASOUT		7	/* Measurement outcome */
#define CQC_TP_GET_TIME		8	/* Get creation time of qubit */
#define CQC_TP_INF_TIME		9	/* Inform about time */
#define CQC_TP_NEW_OK		10 	/* Created new qubit */

#define	CQC_ERR_GENERAL		20	/* General purpose error (no details */
#define	CQC_ERR_NOQUBIT		21	/* No more qubits available */
#define	CQC_ERR_UNSUPP		22	/* Command sequence not supported */
#define	CQC_ERR_TIMEOUT		23	/* Timeout */
#define	CQC_ERR_INUSE		24	/* Qubit already in use */
#define	CQC_ERR_UNKNOWN		25	/* Unknown qubit ID */

/*
	Definitions for the command header and commands.
*/

#define	CQC_CMD_HDR_LENGTH      4
typedef struct
{
	uint16_t qubit_id;	/* Qubit to perform the operation on */
	uint8_t instr;		/* Instruction to execute */
	uint8_t options;	/* Options when executing the command */
} __attribute__((__packed__)) cmdHeader;

/* Possible commands */
#define CQC_CMD_I		0	/* Identity (do nothing, wait one step) */
#define	CQC_CMD_NEW		1	/* Ask for a new qubit */
#define CQC_CMD_MEASURE		2	/* Measure qubit */
#define CQC_CMD_MEASURE_INPLACE	3	/* Measure qubit inplace */
#define CQC_CMD_RESET		4	/* Reset qubit to |0> */
#define CQC_CMD_SEND		5	/* Send qubit to another node */
#define CQC_CMD_RECV		6	/* Ask to receive qubit */
#define CQC_CMD_EPR		7	/* Create EPR pair with the specified node */
#define CQC_CMD_EPR_RECV	8	/* Receive EPR pair */

#define CQC_CMD_X		10	/* Pauli X */
#define CQC_CMD_Z		11	/* Pauli Z */
#define CQC_CMD_Y		12	/* Pauli Y */
#define CQC_CMD_T		13	/* T Gate */
#define CQC_CMD_ROT_X		14	/* Rotation over angle around X in pi/256 increments */
#define CQC_CMD_ROT_Y		15	/* Rotation over angle around Y in pi/256 increments */
#define CQC_CMD_ROT_Z		16	/* Rotation over angle around Z in pi/256 increments */
#define CQC_CMD_H		17	/* Hadamard Gate */
#define CQC_CMD_K		18	/* K Gate - taking computational to Y eigenbasis */

#define CQC_CMD_CNOT		20	/* CNOT Gate with this as control */
#define CQC_CMD_CPHASE		21	/* CPHASE Gate with this as control */

/* Command options */
#define CQC_OPT_NOTIFY		0x01	/* Send a notification when cmd done */
#define CQC_OPT_ACTION		0x02	/* On if there are actions to execute when done */
#define CQC_OPT_BLOCK		0x04	/* Block until command is done */
#define CQC_OPT_IFTHEN		0x08	/* Execute commands depending on outcome */

/* Additional header used to indicate size of a sequence. Used when sending
 * multiple commands at once. It tells the backend how many more messages are
 * coming. */
#define CQC_SEQ_HDR_LENGTH      1
typedef struct
{
        uint8_t cmd_length;     /* The length (in bytes) of messages still to come */
} __attribute__((__packed__)) sequenceHeader;

/* Additional header used to define the rotation angle of a rotation gate. */
#define CQC_ROT_HDR_LENGTH      1
typedef struct
{
        uint8_t step;           /* Angle step of rotation (increments in 1/256 per step) */
} __attribute__((__packed__)) rotationHeader;

/* Additional header used to send a qubit_id. */
#define CQC_QUBIT_HDR_LENGTH    2
typedef struct
{
        uint16_t qubit_id;      /* Qubit_id of the target qubit */
} __attribute__((__packed__)) extraQubitHeader;

/* Additional header used to send to which node to send information to. Used in
 * send and EPR commands. */
#define CQC_COMM_HDR_LENGTH     8
typedef struct
{
	uint16_t remote_app_id;	/* Remote application ID */
	uint16_t remote_port;	/* Port of the remote node for control info */
	uint32_t remote_node;	/* IP of the remote node */
} __attribute__((__packed__)) communicationHeader;

/* Additional header used to send factory information. Factory commands are
 * used to tell the backend to do the following command or a sequence of
 * commands multiple times. */
#define CQC_FACTORY_HDR_LENGTH  2
typedef struct
{
        uint8_t num_iter;       /* Number of iterations to do the sequence */
        uint8_t options;        /* Options when executing the factory */
} __attribute__((__packed__)) factoryHeader;

/* Additional header used to send the outcome of a measurement. */
#define CQC_MEASOUT_HDR_LENGTH  1
typedef struct
{
        uint8_t meas_out;       /* Measurement outcome */
} __attribute__((__packed__)) measoutHeader;

/* Additional header used to send time information (return of
 * CQC_TP_GET_TIME). */
#define CQC_TIMEINFO_HDR_LENGTH 8
typedef struct
{
        uint64_t datetime;      /* Time of creation */
} __attribute__((__packed__)) timeinfoHeader;


/* When an EPR-pair is created the CQC Backend will return information about
 * the entanglement which can be used in a entanglement management
 * protocol. The entanglement information header contains information about the
 * parties that share the EPR-pair, the time of creation, how good the
 * entanglement is (goodness). Furthermore, the entanglement information header
 * contain a entanglement ID (id_AB) which can be used to keep track of the
 * entanglement in the network. The entanglement ID is incremented with respect
 * to the pair of nodes and who initialized the entanglement (DF). For this
 * reason the entanglement ID together with the nodes and the directionality
 * flag gives a unique way to identify the entanglement in the network. */
typedef struct
{
	uint32_t node_A;        /* IP of this node */
	uint16_t port_A;        /* Port of this node */
	uint16_t app_id_A;      /* App ID of this node */
	uint32_t node_B;        /* IP of other node */
	uint16_t port_B;        /* Port of other node */
	uint16_t app_id_B;      /* App ID of other node */
	uint32_t id_AB;		/* Entanglement identifier */
	uint64_t timestamp;	/* Creation time */
	uint64_t tog;		/* Time of goodness */
	uint16_t goodness;	/* Goodness parameter */
	uint8_t df;		/* Directionality flag creation */
	uint8_t unused;		/* Not used - align */
} __attribute__((__packed__)) entanglementHeader;

/*
	CQC Library Definitions
*/

/* Definitions to access and manage CQC */
typedef struct
{
	int sockfd;             /* Socket handling to CQC Backend */
	int app_id;             /* Application details */
} cqc_lib;

/*
 	CQC Function Definitions
*/

cqc_lib * cqc_init(int app_id);
void cqc_error(uint8_t type);
int cqc_connect(cqc_lib *cqc, char *hostname, int portno);
int cqc_cleanup(cqc_lib *cqc);
int cqc_simple_cmd(cqc_lib *cqc,
                   uint8_t command,
                   uint16_t qubit_id,
                   uint8_t notify);
int cqc_full_cmd(cqc_lib *cqc,
                 uint8_t command,
                 uint16_t qubit_id,
                 char notify,
                 char action,
                 char block,
                 uint16_t xtra_id,
                 uint8_t steps,
                 uint16_t r_app_id,
                 uint32_t r_node,
                 uint16_t r_port,
                 uint32_t cmdLength);

int cqc_hello(cqc_lib *cqc);
int cqc_send(cqc_lib *cqc,
             uint16_t qubit_id,
             uint16_t remote_app_id,
             uint32_t remote_node,
             uint16_t remote_port);
uint16_t cqc_recv(cqc_lib *cqc);
int cqc_epr(cqc_lib *cqc,
            uint16_t remote_app_id,
            uint32_t remote_node,
            uint16_t remote_port);
int cqc_measure(cqc_lib *cqc, uint16_t qubit_id);
int cqc_wait_until_done(cqc_lib *cqc, unsigned int reps);
int cqc_wait_until_newok(cqc_lib *cqc);
int cqc_twoqubit(cqc_lib *cqc,
                 uint8_t command,
                 uint16_t qubit1,
                 uint16_t qubit2);
float cqc_tomography_dir(cqc_lib *cqc,
                         uint16_t (*func)(cqc_lib *),
                         uint32_t iter,
                         uint8_t dir);
int cqc_test_qubit(cqc_lib *cqc,
                   uint16_t (*func)(cqc_lib *),
                   uint32_t iter,
                   float epsilon,
                   float exp_x,
                   float exp_y,
                   float exp_z);
int cqc_wait_until_newok(cqc_lib *cqc);

#endif
