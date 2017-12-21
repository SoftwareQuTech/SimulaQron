CQC C Library 
=============

State is kept in the following structure, defined in cqc.h::

	/* Definitions to access and manage CQC */
	typedef struct
	{
		/* Socket handling to CQC Backend */
		int sockfd;

		/* Application details */
		int app_id;
	} cqc_lib;

The following function are available in the library. To execute a specific command, you need to use the right message type as defined in cqc.h. These can also be found in this documentation :doc:`CQCInterface`::

	/*
	 * cqc_init
	 *
	 * Initialize the CQC Backend. Returns a cqc_lib struct used for any further interaction
	 *
	 * Arguments:
	 * app_id	ID to use for this application
	 */
	
	cqc_lib * cqc_init(int app_id)
	
	/* 
	 * cqc_error
	 *
	 * Print the appropriate error message for the error code received.
	 */
	void cqc_error(uint8_t type)
	
	/* 
	 * cqc_connect
	 *
	 * Connect to CQC Backend (if necessary).
	 *
	 * Arguments:
	 * hostname 	hostname to connect to
	 * portno	port number to connect to
	 */
	
	int cqc_connect(cqc_lib *cqc, char *hostname, int portno)
	
	/* 
	 * cqc_cleanup
	 *
	 * Tear down the connection to the CQC Backend (if any) and free the memory of the cqc structure.
	 */
	
	int cqc_cleanup(cqc_lib *cqc)
	
	/*
	 * cqc_simple_cmd
	 *
	 * Executes a simple CQC command (not requiring any additional details)
	 *
	 * Arguments:
	 * command	command identifier to be sent
	 * qubit_id	identifier of qubit on which to perform this command
	 * notify	whether to request a DONE upon completion (0 = no, 1 = yes)
	 */
		
	int cqc_simple_cmd(cqc_lib *cqc, uint8_t command, uint16_t qubit_id, uint8_t notify)
	
	/* 
	 * cqc_full_cmd
	 *
	 * Executes a full CQC command incl extra header
	 *
	 * Arguments:
	 * command	command identifier
	 * qubit_id	qubit to execute on
	 * notify	indication whether notification is requested (0/1)
	 * action	indication whether further actions should be taken following this command (0/1, requires further commands to be sent)
	 * block	indication whether further execution should be suspended while executing this command (0/1)
	 * xtra_id	id of additional qubit
	 * steps	number of steps to rotate or repetitions to perform
	 * r_app_id	remote application id
	 * r_node	remote node (IP)
	 * r_port	remote node port (for classical control info)
	 * cmdLength	length of extra commands to be sent
	 */
	
	int cqc_full_cmd(cqc_lib *cqc, uint8_t command, uint16_t qubit_id, char notify, char action, char block, uint16_t xtra_id, uint8_t steps, uint16_t r_app_id, uint32_t r_node, uint16_t r_port, uint32_t cmdLength)
	
	/*
	 * cqc_hello
	 *
	 * Sends a HELLO message to the CQC Backend.
	 */
	
	int cqc_hello(cqc_lib *cqc)
	
	/*
	 * cqc_send
	 *
	 * Request the qubit to send to remote node.
	 *
	 * Arguments:
	 * qubit_id		qubit to send
	 * remote_app_id  	app id on the remote node to send to
	 * remote_node		address of remote node (IPv6)
	 * remote_port		port for classical control info
	 */
	
	int cqc_send(cqc_lib *cqc, uint16_t qubit_id, uint16_t remote_app_id, uint32_t remote_node, uint16_t remote_port)
	
	/* 
	 * cqc_recv
	 *
	 * Request to receive a qubit. 
	 *
	 * Arguments:
	 * qubit_id		id to assign to this qubit once it is received
	 */
	int cqc_recv(cqc_lib *cqc, uint16_t qubit_id)
		
	/* 
	 * cqc_epr
	 *
	 * Request to generate EPR pair with remote node.
	 *
	 * Arguments:
	 * remote_app_id	app id on the remote node to send to
	 * remote_node		address of remote node to receive from (IPv6)
	 * remote_port		port for classical control info
	 */
	int cqc_epr(cqc_lib *cqc, uint16_t remote_app_id, uint32_t remote_node, uint16_t remote_port)
	
	/*
	 * cqc_measure
	 *
	 * Request to measure a specific qubit. This will block until the reply is received. 
	 * (Non blocking measure requests can be performed using cqc_simple_cmd)
	 *
	 * Arguments:
	 * qubit_id		qubit to measure
	 */
	
	int cqc_measure(cqc_lib *cqc, uint16_t qubit_id)
	
	/* 
	 * cqc_wait_until_done
	 *
	 * Read a certain number of DONE commands before proceeding.
	 *
	 * Arguments:
	 * reps	number of replies to wait for
	 */
	int cqc_wait_until_done(cqc_lib *cqc, unsigned int reps)
	
	/*
	 *  cqc_twoqubit
	 * 
	 *  Execute local two qubit gate.
	 *
	 *  Arguments:
	 *  command     command id to execute
	 *  qubit1      number of the first qubit
	 *  qubit2	number of the second qubit
	 */
	
	int cqc_twoqubit(cqc_lib *cqc, uint8_t command, uint16_t qubit1, uint16_t qubit2)
	
	
	
