#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
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
        memset((char *) cqc, 0x00, sizeof(cqc_lib));
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
                fprintf(stderr,"CQC ERROR: No more qubits available.\n");
                break;
        case CQC_ERR_UNSUPP:
                fprintf(stderr,"CQC ERROR: Command not supported.\n");
                break;
        case CQC_ERR_TIMEOUT:
                fprintf(stderr,"CQC ERROR: Timeout.\n");
                break;
        case CQC_ERR_INUSE:
                fprintf(stderr,"CQC ERROR: Qubit already in use.\n");
                break;
        case CQC_ERR_UNKNOWN:
                fprintf(stderr,"CQC ERROR: Unknown qubit ID.");
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
 * hostname     hostname to connect to
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

        memset((char *) &serv_addr, 0x00, sizeof(serv_addr));
        serv_addr.sin_family = AF_INET;
        memmove((char *)&serv_addr.sin_addr.s_addr,
                (char *)server->h_addr_list[0],
                server->h_length);
        serv_addr.sin_port = htons(portno);

        /* Now connect to the server */
        if (connect(sock,
                    (struct sockaddr*)&serv_addr,
                    sizeof(serv_addr)) < 0) {
                perror("ERROR - Cannot connect");
                return(-1);
        }
        cqc->sockfd = sock;
        return(0);
}

/*
 * cqc_cleanup
 *
 * Tear down the connection to the CQC Backend (if any) and free the memory of
 * the cqc structure.
 */
int
cqc_cleanup(cqc_lib *cqc)
{
        close(cqc->sockfd);
        free(cqc);

        return(0);
}

/*
 * send_cqc_header
 *
 * Prepare and sends CQC header
 */
static int
send_cqc_header(cqc_lib *cqc, uint8_t type, uint32_t len)
{
        int n;
        cqcHeader cqcH;

        cqcH.version = CQC_VERSION;
        cqcH.type = type;
        cqcH.app_id = htons(cqc->app_id);
        cqcH.length = htonl(len);

        /* Send message to the server */
        n = write(cqc->sockfd, &cqcH, CQC_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR writing to socket");
                return(-1);
        }
        return(n);
}

/*
 * send_cqc_cmd
 *
 * Build and send the CQC header and the command header
 *
 * Arguments:
 * command	command identifier to be sent
 * qubit_id	identifier of qubit on which to perform this command
 * notify	whether to request a DONE upon completion
 * length       length of any headers that are to follow
 */
static int
send_cqc_cmd(cqc_lib *cqc,
        uint8_t command,
        uint16_t qubit_id,
        bool notify,
        bool action,
        bool block,
        uint32_t length)
{
        int n, nt;
        cmdHeader cmdH;

        /* Send CQC message indicating a command */
        nt = send_cqc_header(cqc, CQC_TP_COMMAND, CQC_CMD_HDR_LENGTH + length);

        /* Prepare message for the specific command */
        memset(&cmdH, 0x00, sizeof(cmdH));
        cmdH.qubit_id = htons(qubit_id);
        cmdH.instr = command;
        if (notify) {
                cmdH.options = cmdH.options | CQC_OPT_NOTIFY;
        }
        if (action) {
                cmdH.options = cmdH.options | CQC_OPT_ACTION;
        }
        if (block) {
                cmdH.options = cmdH.options | CQC_OPT_BLOCK;
        }

        /* Send message to the server */
        n = write(cqc->sockfd, &cmdH, CQC_CMD_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR writing to socket");
                return(-1);
        }
        nt += n;

        return(nt);
}

/*
 * cqc_hello
 *
 * Sends a HELLO message to the CQC Backend.
 */
int
cqc_hello(cqc_lib *cqc)
{
        return(send_cqc_header(cqc, CQC_TP_HELLO, 0));
}

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
int
cqc_simple_cmd(cqc_lib *cqc,
               uint8_t command,
               uint16_t qubit_id,
               bool notify)
{
        return(send_cqc_cmd(cqc, command, qubit_id, notify, false, notify, 0));
}

/*
 * cqc_send
 *
 * Request the qubit to send to remote node.
 *
 * Arguments:
 * qubit_id		qubit to send
 * remote_app_id        app id on the remote node to send to
 * remote_node		address of remote node (IPv6)
 * remote_port		port for classical control info
 */

int
cqc_send(cqc_lib *cqc,
         uint16_t qubit_id,
         uint16_t remote_app_id,
         uint16_t remote_port,
         uint32_t remote_node)
{
        int n, nt;
        commHeader commH;

        nt = send_cqc_cmd(cqc,
                          CQC_CMD_SEND,
                          qubit_id,
                          true,
                          false,
                          true,
                          CQC_COMM_HDR_LENGTH);

        /* Prepare message for the specific command */
        memset(&commH, 0x00, sizeof(commH));
        commH.remote_app_id = remote_app_id;
        commH.remote_port = remote_port;
        commH.remote_node = remote_node;

        /* Send message to the server */
        n = write(cqc->sockfd, &commH, CQC_COMM_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR writing to socket");
                return(-1);
        }
        nt += n;

        return(nt);
}

/*
 * cqc_recv
 *
 * Request to receive a qubit.
 *
 * Arguments:
 * qubit_id		id to assign to this qubit once it is received
 */
uint16_t
cqc_recv(cqc_lib *cqc)
{
        int n;
        cqcHeader reply;
        qubitHeader note;

        /* Send out request to receive a qubit */
        n = cqc_simple_cmd(cqc, CQC_CMD_RECV, 0, 0);
        if (n < 0) {
                perror("ERROR - Cannot send receive request");
                return(-1);
        }

        /* Now read CQC Header from server response */
        memset(&reply, 0x00, sizeof(reply));
        n = read(cqc->sockfd, &reply, CQC_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get reply header");
                return(-1);
        }
        if(reply.type != CQC_TP_RECV) {
                fprintf(stderr,"ERROR: Expected RECV");
                return(-1);
        }

        /* Then read qubit id from notify header */
        memset(&note, 0x00, sizeof(note));
        n = read(cqc->sockfd, &note, CQC_QUBIT_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get measurement outcome");
                return(-1);
        }

        return(ntohs(note.qubit_id));
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
cqc_measure(cqc_lib *cqc, uint16_t qubit_id)
{
        int n;
        cqcHeader reply;
        measoutHeader note;

        /* Send command to perform measurement */
        cqc_simple_cmd(cqc, CQC_CMD_MEASURE, qubit_id, 0);

        /* Now read CQC Header from server response */
        memset(&reply, 0x00, sizeof(reply));
        n = read(cqc->sockfd, &reply, CQC_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get reply header");
                return(-1);
        }
        if(reply.type != CQC_TP_MEASOUT) {
                fprintf(stderr,"ERROR: Expected MEASOUT, got %u\n",reply.type);
                return(-1);
        }

        /* Then read measurement outcome from notify header */
        memset(&note, 0x00, sizeof(note));
        n = read(cqc->sockfd, &note, CQC_MEASOUT_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get measurement outcome");
                return(-1);
        }

        return(note.meas_out);
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
                memset(&reply, 0x00, sizeof(reply));
                n = read(cqc->sockfd, &reply, CQC_HDR_LENGTH);
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
 * cqc_wait_until_newok
 *
 * Wait until qubit creation is confirmed. Returns qubit id if successful, -1 otherwise.
 *
 */
int
cqc_wait_until_newok(cqc_lib *cqc)
{
        int n;
        cqcHeader reply;
        qubitHeader note;

        /* Now read CQC Header from server response */
        memset(&reply, 0x00, sizeof(reply));
        n = read(cqc->sockfd, &reply, CQC_HDR_LENGTH);
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
        if(reply.type != CQC_TP_NEW_OK) {
                fprintf(stderr,"Unexpected reply of type %d, expected %d\n",reply.type, CQC_TP_NEW_OK);
                return(-1);
        }

        /* Then read qubit id from notify header */
        memset(&note, 0x00, sizeof(note));
        n = read(cqc->sockfd, &note, CQC_QUBIT_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get measurement outcome");
                return(-1);
        }

        return(ntohs(note.qubit_id));
}

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
int
cqc_twoqubit(cqc_lib *cqc,
             uint8_t command,
             uint16_t qubit1,
             uint16_t qubit2)
{
        int n, nt;
        qubitHeader qubitH;

        nt = send_cqc_cmd(cqc,
                          command,
                          qubit1,
                          false,
                          false,
                          true,
                          CQC_QUBIT_HDR_LENGTH);

        /* Prepare message for the specific command */
        memset(&qubitH, 0x00, sizeof(qubitH));
        qubitH.qubit_id = qubit2;

        /* Send message to the server */
        n = write(cqc->sockfd, &qubitH, CQC_QUBIT_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR writing to socket");
                return(-1);
        }
        nt += n;

        return(nt);
}

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
int
cqc_epr(cqc_lib *cqc,
        uint16_t remote_app_id,
        uint16_t remote_port,
        uint32_t remote_node,
        entanglementHeader *ent_info)
{
        int n, nt;
        commHeader commH;
        cqcHeader reply;
        qubitHeader note;

        nt = send_cqc_cmd(cqc,
                          CQC_CMD_EPR,
                          0,
                          true,
                          false,
                          true,
                          CQC_COMM_HDR_LENGTH);

        /* Prepare message for the specific command */
        memset(&commH, 0x00, sizeof(commH));
        commH.remote_app_id = remote_app_id;
        commH.remote_port = remote_port;
        commH.remote_node = remote_node;

        /* Send message to the server */
        n = write(cqc->sockfd, &commH, CQC_COMM_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR writing to socket");
                return (-1);
        }
        nt += n;

        /* Now read CQC Header from server response */
        memset(&reply, 0x00, sizeof(reply));
        n = read(cqc->sockfd, &reply, CQC_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get reply header");
                return (-1);
        }
        if (reply.type != CQC_TP_MEASOUT) {
                fprintf(stderr, "ERROR: Expected MEASOUT, got %u\n", reply.type);
                return (-1);
        }

        /* Then read qubit id from notify header */
        memset(&note, 0x00, sizeof(note));
        n = read(cqc->sockfd, &note, CQC_QUBIT_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get measurement outcome");
                return (-1);
        }

        /* Read the entanglement header */
        memset(ent_info, 0x00, sizeof(*ent_info));
        n = read(cqc->sockfd, ent_info, CQC_ENT_INFO_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get entanglement  info header");
        }

        return (note.qubit_id);
}

/*
 * cqc_epr_recv
 *
 * Request to receive EPR pair.
 *
 */
int
cqc_epr_recv(cqc_lib *cqc,
             entanglementHeader * ent_info)
{
        int n, nt;
        cqcHeader reply;
        qubitHeader note;

        nt = send_cqc_cmd(cqc,
                          CQC_CMD_EPR_RECV,
                          0,
                          true,
                          false,
                          true,
                          CQC_COMM_HDR_LENGTH);
        if (nt < 0) {
                perror("ERROR - failed to send");
                return (-1);
        }

        /* Now read CQC Header from server response */
        memset(&reply, 0x00, sizeof(reply));
        n = read(cqc->sockfd, &reply, CQC_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get reply header");
                return (-1);
        }
        if (reply.type != CQC_TP_MEASOUT) {
                fprintf(stderr, "ERROR: Expected MEASOUT, got %u\n", reply.type);
                return (-1);
        }

        /* Then read qubit id from notify header */
        memset(&note, 0x00, sizeof(note));
        n = read(cqc->sockfd, &note, CQC_QUBIT_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get measurement outcome");
                return (-1);
        }

        /* Read the entanglement header */
        memset(ent_info, 0x00, sizeof(*ent_info));
        n = read(cqc->sockfd, ent_info, CQC_ENT_INFO_HDR_LENGTH);
        if (n < 0) {
                perror("ERROR - cannot get entanglement  info header");
        }

        return (note.qubit_id);
}
