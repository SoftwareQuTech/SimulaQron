Example using the C library
===========================

The following example involves two nodes Alice and Bob. It is assumed that you already started the SimulaQron backend, as well as the CQC Backend. The code below will simply transmit a qubit from Alice to Bob. In the examples below, we will assume that the CQC Backend has been setup using the default configuration file::

	# Network configuration file
	#
	# For each host its informal name, as well as its location in the network must
	# be listed.
	#
	# [name], [hostname], [port number]
	#

	Alice, localhost, 8821
	Bob, localhost, 8822

^^^^^^^^^^^^^^^
Code for Alice
^^^^^^^^^^^^^^^

The following code can be found in cqc/cLib and be compiled using make; make send. After compilation, run the code using::

	./send localhost 8821 localhost 8822

.. note:: It the compiling fails for you (in particular on macOS). Try using `clang` instead of `gcc`, by changing the entry :code:`CC` in the file `MakeFile`.

Here, both Alice and Bob run on the same host (localhost) but on different ports for testing purposes. To allow the transmission of associated classical control information, the port of Bob's CQC Backend must also be specified.:: 

	#include <stdio.h>
	#include <unistd.h>
	#include <stdlib.h>
	#include <sys/types.h>
	#include <sys/socket.h>
	
	#include <netinet/in.h>
	#include <netdb.h>
	
	#include <string.h>
	#include<arpa/inet.h>
	 
	
	#include "cqc.h"
	
	int main(int argc, char *argv[]) {
	
		uint16_t portno;
		char *hostname;
		uint16_t remotePort;
		char *remoteHost;
		struct in_addr remoteNode;
		cqc_lib *cqc;
		int app_id;
		int outcome;
		struct hostent *server;
	
		/* Retrieve arguments from command line */
	   	if (argc < 5) {
	      		fprintf(stderr,"usage %s hostname port remoteHost remotePort\n", argv[0]);
	      		exit(0);
	   	}
		hostname = argv[1];	
	   	portno = atoi(argv[2]);
		remoteHost = argv[3];
		remotePort = atoi(argv[4]);
	
		/* Lookup remote host */
	        server = gethostbyname(remoteHost);
	        if (server == NULL) {
	                fprintf(stderr,"ERROR, no such host\n");
	                return(-1);
	        }
	
		/* In this example, we are simply application 10 */
		app_id = 10;
	
		/* In this example, we will not check for errors. All functions return -1 on failure */
		cqc = cqc_init(app_id);
		cqc_connect(cqc, hostname, portno);
	
		cqc_simple_cmd(cqc, CQC_CMD_NEW, 0);
		cqc_wait_until_done(cqc, 1);
	
		remoteNode.s_addr = ntohl(*((uint32_t *)server->h_addr));
		cqc_send(cqc, 0, app_id, remoteNode.s_addr, remotePort);
		cqc_wait_until_done(cqc, 1);
	
	   	return 0;
	}

^^^^^^^^^^^^^
Code for Bob 
^^^^^^^^^^^^^

The following code can be found in cqc/cLib and be compiled using make; make recv. After compilation, run the code using::

	testSend localhost 8822 localhost 8821 

Here, both Alice and Bob run on the same host (localhost) but on different ports for testing purposes. To allow the transmission of associated classical control information, the port of Alice's CQC Backend must also be specified. No actions are taken after the transmission is completed. 

You may be wondering: why is Bob calling recv? In full analogy to classical socket programming, Bob will issue a request to receive a qubit. This merely registers the intention to be notified, once a qubit for the application ID is delivered to Bob's node. Once a qubit is actually received, a notification is sent that the qubit has arrived and you may device to perform further processing on the qubit data received, such as adding gates to be executed.:: 


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
	
	int main(int argc, char *argv[]) {
	
		uint16_t portno;
		char *hostname;
		uint16_t remotePort;
		char *remoteHost;
		struct in_addr remoteNode;
		cqc_lib *cqc;
		int app_id;
		int outcome;
		struct hostent *server;
	
		/* Retrieve arguments from command line */
	   	if (argc < 5) {
	      		fprintf(stderr,"usage %s hostname port remoteHost remotePort\n", argv[0]);
	      		exit(0);
	   	}
		hostname = argv[1];	
	   	portno = atoi(argv[2]);
		remoteHost = argv[3];
		remotePort = atoi(argv[4]);
	
		/* Lookup remote host */
	        server = gethostbyname(remoteHost);
	        if (server == NULL) {
	                fprintf(stderr,"ERROR, no such host\n");
	                return(-1);
	        }
	
		/* In this example, we are simply application 10 */
		app_id = 10;
	
		/* In this example, we will not check for errors. All functions return -1 on failure */
		cqc = cqc_init(app_id);
		cqc_connect(cqc, hostname, portno);
	
		cqc_recv(cqc, 0);
		cqc_wait_until_done(cqc, 1);
	
	   	return 0;
	}
		
