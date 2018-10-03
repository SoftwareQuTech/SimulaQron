CQC Interface 
=============

Here we specifiy the CQC message interface. For programming SimulaQron via the CQC Interface using the Python or C provided, you do not need to know the extend of this message format. The below will be necessary, if you want to write your own library in another language. The easiest way of programming SimulaQron is via the Python CQC lib, so we recommend to get started there. 

Upon establishing a connection to the CQC Backend, the following packet format can be used to issue commands to the simulated quantum network. Each interaction to and from the interface starts with a CQC Header, followed by additional headers as appropriate to the message type. 

When accessing the interface directly, you must keep track of qubit IDs for each application ID yourself. It is a deliberate choice that the CQC Backend does not itself keep track of qubit or application IDs, leaving such management to you (and indeed higher levels of abstraction if you wish).

^^^^^^^^^^
CQC Header
^^^^^^^^^^
=========== ============================  =========  ===============================================================
Function  	Type
=========== ============================  =========  ===============================================================
version	     unsigned integer (uint8_t)    1 byte      Current version is 0
type	     unsigned integer (uint8_t)    1 byte      Message type (see below)
app_id	     unsigned integer (uint16_t)   2 bytes     Application ID, return messages will be tagged appropriately 
length	     unsigned integer (uint32_t)   4 bytes     Total length of the CQC instruction packet
=========== ============================  =========  ===============================================================

Possible message types are listed below. Depending on the message type additional headers may be required as specified below.::

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

	#define	CQC_ERR_GENERAL		20	/* General purpose error (no details */
	#define	CQC_ERR_NOQUBIT		21	/* No more qubits available */
	#define	CQC_ERR_UNSUPP		22	/* Command sequence not supported */
	#define	CQC_ERR_TIMEOUT		23	/* Timeout */
	#define CQC_ERR_INUSE		24	/* Qubit ID in use when requesting new ID */

^^^^^^^^^^^^^^^^^^
CQC Command Header
^^^^^^^^^^^^^^^^^^

If the message type is CQC_TP_COMMAND, CQC_TP_FACTORY or CQC_TP_GET_TIME, then the following additional command header must be supplied. It identifies the specific instruction to execute, as well as the qubit ID on which to perform this instructions. For rotations, two qubit gates, request to send or receive, and produce entanglement, the CQC Xtra Header is required supplying further information

=========== ============================  ==========  ===============================================================
 Function     Type                         Length      Comment
=========== ============================  ==========  ===============================================================
qubit_id     unsigned int (uint16_t)       2 bytes     Qubit ID to perform the operation on
instr	     unsigned int (uint8_t)        1 byte      Instruction to perform (see below)
options	     unsigned int (uint8_t)        1 byte      Options when executing the command
=========== ============================  ==========  ===============================================================

The value of instr can be any of the following::

	/* Possible commands */
	#define CQC_CMD_I		0	/* Identity (do nothing, wait one step) */
	#define	CQC_CMD_NEW		1	/* Ask for a new qubit */
	#define CQC_CMD_MEASURE		2	/* Measure qubit */
	#define CQC_CMD_MEASURE_INPLACE	3	/* Measure qubit inplace */
	#define CQC_CMD_RESET		4	/* Reset qubit to |0> */
	#define CQC_CMD_SEND		5	/* Send qubit to another node */
	#define CQC_CMD_RECV		6	/* Ask to receive qubit */
	#define CQC_CMD_EPR		7	/* Create EPR pair with the specified node */

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

^^^^^^^^^^^^^^^
CQC Xtra Header
^^^^^^^^^^^^^^^

Additional header containing further information. 
The following commands require an xtra header when issued to the CQC Backend: CQC_CMD_SEND, CQC_CMD_RECV, CQC_CMD_CPHASE, CQC_CMD_CNOT, CQC_CMD_ROT_X, CQC_CMD_ROT_Y, CQC_CMD_ROT_Z

============== ============================  ==========  ===============================================================
Function	Type			      Length	  Comments
============== ============================  ==========  ===============================================================
xtra_qubit_id	unsigned int (uint16_t)	      2 bytes	   ID of the target qubit in a 2 qubit controlled gate
remote_app_id   unsigned int (uint16_t)       2 bytes	   Remote Application ID
remote_node	unsigned int (uint32_t)       4 bytes	   IP of the remote node (IPv4)
cmdLength	unsigned int (uint32_t)       4 bytes      Length of the additional commands to execute upon completion.
remote_port	unsigned int (uint16_t)	      2 bytes	   Port of the remode node for sending classical control info
steps		unsigned int (uint8_t) 	      1 byte 	   Angle step of rotation (ROT) OR number of repetitions (FACTORY)
unused		unsigned int (uint8_t)	      1 byte	   4 byte align
============== ============================  ==========  ===============================================================

^^^^^^^^^^^^^^^^^
CQC Notify Header
^^^^^^^^^^^^^^^^^

In some cases, the CQC Backend will return notifications to the client that require additional information. For example, where a qubit was received from, the lifetime of a qubit, the measurement outcome etc. 

============== ============================  ==========  ===============================================================
Function	Type			      Length	   Comments
============== ============================  ==========  ===============================================================
qubit_id	unsigned int (uint16_t)	      2 bytes	  ID of the received qubit
remote_app_id   unsigned int (uint16_t)       2 bytes     Remote application ID
remote_node	unsigned int (uint32_t)	      4 bytes     IP of the remote node
remote_port     unsigned int (uint16_t)       2 bytes     Port of the remote node for sending classical control info
outcome		unsigned int (uint8_t)	      1 byte      Measurement outcome
unused		unsigned int (uint8_t)	      1 byte	  4 byte align
============== ============================  ==========  ===============================================================



