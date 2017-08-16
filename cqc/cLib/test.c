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

	cqc_simple_cmd(cqc, CQC_CMD_NEW, 0);
	cqc_wait_until_done(cqc, 1);

	remoteNode.s_addr = ntohl(*((uint32_t *)server->h_addr));
	printf("Node %u\n",remoteNode.s_addr);
	cqc_send(cqc, 0, 0, remoteNode.s_addr, remotePort);
	cqc_wait_until_done(cqc, 1);

	//cqc_simple_cmd(cqc, CQC_CMD_NEW, 1);
	// cqc_wait_until_done(cqc, 1);

	//cqc_simple_cmd(cqc, CQC_CMD_I, 0);
	//cqc_wait_until_done(cqc, 1);

	cqc_simple_cmd(cqc, CQC_CMD_H,0);
	cqc_wait_until_done(cqc, 1);

	outcome = cqc_measure(cqc, 0);
	printf("Outcome: %d\n",outcome);
	// cqc_twoqubit(cqc,CQC_CMD_CPHASE, 0, 1);
	// cqc_wait_until_done(cqc, 1);
		
	
   	return 0;
}
