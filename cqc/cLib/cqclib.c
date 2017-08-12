#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>

// #include <stdlib.h>

#include <netinet/in.h>
#include <netdb.h>

#include <string.h>

#include "cqc.h"

/*
 * cqc_init
 *
 * Initialize the CQC Backend.
 *
 * Arguments:
 * app_id	ID to use for this application
 */

cqc_lib *
cqc_init(int app_id)
{
	cqc_lib *cqc;

	/* Initialize CQC Data structure */
	cqc = (cqc_lib *)malloc(sizeof(cqc_lib));
	bzero((char *) cqc, sizeof(cqc_lib));
	cqc->app_id = app_id;

	return(cqc);
}

/* 
 * cqc_error
 *
 * Print the appropriate error message for the error code received.
 */
void
cqc_error(uint8_t type)
{
	switch(type) {
		case CQC_ERR_GENERAL:
			fprintf(stderr,"CQC ERROR: General error.\n");
			break;
		case CQC_ERR_NOQUBIT:
			fprintf(stderr,"CQC ERROR: No qubit with the specified ID for this application.\n");
			break;
		case CQC_ERR_UNSUPP:
			fprintf(stderr,"CQC ERROR: Command not supported by implementation.\n");
			break;
		case CQC_ERR_TIMEOUT:
			fprintf(stderr,"CQC ERROR: Timeout.\n");
			break;
		case CQC_ERR_INUSE:
			fprintf(stderr,"CQC ERROR: Qubit ID already in use.\n");
			break;
		default:
			fprintf(stderr,"CQC ERROR: Unknown error type.\n");
	}
	return;
}

/* 
 * cqc_connect
 *
 * Connect to CQC Backend (if necessary).
 *
 * Arguments:
 * hostname 	hostname to connect to
 * portno	port number to connect to
 */

int
cqc_connect(cqc_lib *cqc, char *hostname, int portno)
{
	int sock;
	struct sockaddr_in serv_addr;
	struct hostent *server;

	/* Set up connection details */	
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
                perror("ERROR opening socket");
		return(-1);
        }
        
        server = gethostbyname(hostname);
        if (server == NULL) {
                fprintf(stderr,"ERROR, no such host\n");
		return(-1);
        }

	bzero((char *) &serv_addr, sizeof(serv_addr));
   	serv_addr.sin_family = AF_INET;
   	bcopy((char *)server->h_addr, (char *)&serv_addr.sin_addr.s_addr, server->h_length);
   	serv_addr.sin_port = htons(portno);

   	/* Now connect to the server */
   	if (connect(sock, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0) {
      		perror("ERROR - Cannot connect");
		return(-1);
   	}
	cqc->sockfd = sock;
	return(0);
}

/* 
 * cqc_cleanup
 *
 * Tear down the connection to the CQC Backend (if any) and free the memory of the cqc structure.
 */

int 
cqc_cleanup(cqc_lib *cqc)
{	

	close(cqc->sockfd);
	free(cqc);

	return(0);
}

/*
 * cqc_simple_cmd
 *
 * Executes a simple CQC command (not requiring any additional details)
 *
 * Arguments:
 * command	command identifier to be sent
 * qubit_id	identifier of qubit on which to perform this command
 */
	
int 
cqc_simple_cmd(cqc_lib *cqc, uint8_t command, uint8_t qubit_id)
{
	int n;
	cqcHeader cqcH;
	cmdHeader cmdH;

	/* Prepare CQC message indicating a command */
	cqcH.version = CQC_VERSION;
	cqcH.app_id = cqc->app_id;
	cqcH.type = CQC_TP_COMMAND;
	cqcH.length = CQC_CMD_HDR_LENGTH;
   
   	/* Send message to the server */
   	n = write(cqc->sockfd, &cqcH, CQC_HDR_LENGTH);
   	if (n < 0) {
      		perror("ERROR writing to socket");
		return(-1);
   	}

	/* Prepare message for the specific command */
	bzero(&cmdH, sizeof(cmdH));
	cmdH.qubit_id = qubit_id;
	cmdH.instr = command;
	cmdH.options = 0;

   	/* Send message to the server */
   	n = write(cqc->sockfd, &cmdH, CQC_CMD_HDR_LENGTH);
   	if (n < 0) {
      		perror("ERROR writing to socket");
      		return(-1);
   	}

	return(n);
}

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
 * cmdLength	length of extra commands to be sent
 */

int
cqc_full_cmd(cqc_lib *cqc, uint8_t command, uint8_t qubit_id, char notify, char action, char block, uint8_t xtra_id, uint8_t steps, uint16_t r_app_id, uint64_t r_node, uint32_t cmdLength)
{
	int n;
	cqcHeader cqcH;
	cmdHeader cmdH;
	xtraCmdHeader xtra;

	/* Prepare CQC message indicating a command */
	cqcH.version = CQC_VERSION;
	cqcH.app_id = cqc->app_id;
	cqcH.type = CQC_TP_COMMAND;
	cqcH.length = CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH;
   
   	/* Send message to the server */
   	n = write(cqc->sockfd, &cqcH, CQC_HDR_LENGTH);
   	if (n < 0) {
      		perror("ERROR writing to socket");
		return(-1);
   	}

	/* Prepare message for the specific command */
	bzero(&cmdH, sizeof(cmdH));
	cmdH.qubit_id = qubit_id;
	cmdH.instr = command;

	cmdH.options = 0;
	if(notify == 1) {
		cmdH.options = cmdH.options | CQC_OPT_NOTIFY;
	}
	if(action == 1) {
		cmdH.options = cmdH.options | CQC_OPT_ACTION;
	}
	if(block == 1) {
		cmdH.options = cmdH.options | CQC_OPT_BLOCK;
	}
   	/* Send message to the server */
   	n = write(cqc->sockfd, &cmdH, CQC_CMD_HDR_LENGTH);
   	if (n < 0) {
      		perror("ERROR writing to socket");
      		return(-1);
   	}

	/* Prepare extra heeader */
	bzero(&xtra, sizeof(xtra));
	xtra.xtra_qubit_id = xtra_id;
	xtra.steps = steps;
	xtra.remote_app_id = r_app_id;
	xtra.remote_node = r_node;
	xtra.cmdLength = cmdLength;
   	/* Send message to the server */
   	n = write(cqc->sockfd, &xtra, CQC_CMD_XTRA_LENGTH);
   	if (n < 0) {
      		perror("ERROR writing to socket");
      		return(-1);
   	}

	return(n);
}

/*
 * cqc_hello
 *
 * Sends a HELLO message to the CQC Backend.
 */

int
cqc_hello(cqc_lib *cqc)
{
	int n;
	cqcHeader cqcH;

	/* Prepare CQC message indicating a command */
	cqcH.version = CQC_VERSION;
	cqcH.app_id = cqc->app_id;
	cqcH.type = CQC_TP_HELLO;
	cqcH.length = CQC_CMD_HDR_LENGTH;
   
   	/* Send message to the server */
   	n = write(cqc->sockfd, &cqcH, CQC_HDR_LENGTH);
   	if (n < 0) {
      		perror("ERROR writing to socket");
		return(-1);
   	}
	return(n);
}

/*
 * cqc_send
 *
 * Request the qubit to send to remote node.
 *
 * Arguments:
 * qubit_id		qubit to send
 * remote_app_id  	app id on the remote node to send to
 * remote_node		address of remote node (IPv6)
 */

int
cqc_send(cqc_lib *cqc, uint8_t qubit_id, uint16_t remote_app_id, uint64_t remote_node)
{
	return(cqc_full_cmd(cqc, CQC_CMD_SEND, qubit_id, 0, 0, 1, 0, 0, remote_app_id, remote_node, 0));
}

/* 
 * cqc_recv
 *
 * Request to receive a qubit. 
 *
 * Arguments:
 * qubit_id		id to assign to this qubit once it is received
 * remote_app_id	app id on the remote node to send to
 * remote_node		address of remote node to receive from (IPv6)
 */
int
cqc_recv(cqc_lib *cqc, uint8_t qubit_id, uint16_t remote_app_id, uint64_t remote_node)
{
	return(cqc_full_cmd(cqc, CQC_CMD_RECV, qubit_id, 0, 0, 1, 0, 0, remote_app_id, remote_node, 0));
}
	
/* 
 * cqc_epr
 *
 * Request to generate EPR pair with remote node.
 *
 * Arguments:
 * remote_app_id	app id on the remote node to send to
 * remote_node		address of remote node to receive from (IPv6)
 */
int
cqc_epr(cqc_lib *cqc, uint16_t remote_app_id, uint64_t remote_node)
{
	return(cqc_full_cmd(cqc, CQC_CMD_RECV, 0, 0, 0, 1, 0, 0, remote_app_id, remote_node, 0));
}	

/*
 * cqc_measure
 *
 * Request to measure a specific qubit. This will block until the reply is received. 
 * (Non blocking measure requests can be performed using cqc_simple_cmd)
 *
 * Arguments:
 * qubit_id		qubit to measure
 */

int
cqc_measure(cqc_lib *cqc, uint8_t qubit_id)
{
	int n;
	cqcHeader reply;
	notifyHeader note;

	n = cqc_simple_cmd(cqc, CQC_CMD_MEASURE, qubit_id);
	if (n < 0) {
		perror("ERROR - measurement failed");
		return(-1);
	}

  	/* Now read CQC Header from server response */
   	bzero(&reply, sizeof(reply));
   	n = read(cqc->sockfd, &reply, sizeof(reply));
   	if (n < 0) {
      		perror("ERROR - cannot get reply header");
      		return(-1);
   	}	

   	bzero(&note, sizeof(note));
   	n = read(cqc->sockfd, &note, sizeof(note));
   	if (n < 0) {
      		perror("ERROR - cannot get measurement outcome");
      		return(-1);
   	}	

	return(note.outcome);
}

/* 
 * cqc_wait_until_done
 *
 * Read a certain number of DONE commands before proceeding.
 *
 * Arguments:
 * reps	number of replies to wait for
 */
int
cqc_wait_until_done(cqc_lib *cqc, unsigned int reps)
{
	int i, n;
	cqcHeader reply;

	for(i = 0; i < reps; i++) {
  		/* Now read CQC Header from server response */
   		bzero(&reply, sizeof(reply));
   		n = read(cqc->sockfd, &reply, sizeof(reply));
   		if (n < 0) {
      			perror("ERROR - cannot get reply header");
      			return(-1);
   		}	

		/* Check whether an error occured */
		if(reply.type >= CQC_ERR_GENERAL) {
			cqc_error(reply.type);
			return(-1);
		}

		/* Otherwise check whether it's done */
		if(reply.type != CQC_TP_DONE) {
			fprintf(stderr,"Unexpected reply of type %d\n",reply.type);
			return(-1);
		}
	}
	return(0);
}

/*
 *  cqc_twoqubit
 * 
 *  Execute local two qubit gate.
 */

int
cqc_twoqubit(cqc_lib *cqc, uint8_t command, uint8_t qubit1, uint8_t qubit2)
{
	return(cqc_full_cmd(cqc, command, qubit1, 0, 0, 1, qubit2, 0, 0, 0, 0));
}

int main(int argc, char *argv[]) {

	int portno;
	char *hostname;
	cqc_lib *cqc;
	int app_id;

	/* Retrieve arguments from command line */
   	if (argc < 3) {
      		fprintf(stderr,"usage %s hostname port\n", argv[0]);
      		exit(0);
   	}
	hostname = argv[1];	
   	portno = atoi(argv[2]);

	/* In this example, we are simply application 10 */
	app_id = 10;

	/* In this example, we will not check for errors. All functions return -1 on failure */

	cqc = cqc_init(app_id);
	cqc_connect(cqc, hostname, portno);

	cqc_simple_cmd(cqc, CQC_CMD_NEW, 0);
	cqc_wait_until_done(cqc, 1);

	cqc_simple_cmd(cqc, CQC_CMD_NEW, 1);
	cqc_wait_until_done(cqc, 1);

	cqc_simple_cmd(cqc, CQC_CMD_I, 0);
	cqc_wait_until_done(cqc, 1);

	cqc_simple_cmd(cqc, CQC_CMD_X, 0);
	cqc_wait_until_done(cqc, 1);

	cqc_twoqubit(cqc,CQC_CMD_CPHASE, 0, 1);
	cqc_wait_until_done(cqc, 1);
		
	
   	return 0;
}
