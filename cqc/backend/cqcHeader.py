

from struct import *

# Constant defining CQC version
CQC_VERSION=0

# Constants defining the messages types
CQC_HELLO=0	# Alive check
CQC_COMMAND=1	# Execute a command list
CQC_FACTORY=2 	# Start executing command list repeatedly
CQC_EXPIRE=3	# Qubit has expired
CQC_DONE=4	# Done with command
CQC_RECV=5	# Received qubit
CQC_EPR_OK=6	# Created EPR pair
CQC_MEASOUT=7	# Measurement outcome

CQC_ERR_GENERAL=20 # General purpose error (no details
CQC_ERR_NOQUBIT=21 # No more qubits available
CQC_ERR_UNSUPP=22 # No sequence not supported
CQC_ERR_TIMEOUT=23 # Timeout

class CQCHeader:

	def __init__(self):
		self.version = 0;
		self.type = -1;
		self.app_id = 0;

	def __init__(self, headerBytes):
		self.unpackHeader(headerBytes);


	def unpackHeader(self, headerBytes):

		cqcH = unpack("BBH", headerBytes);

		self.version = cqcH[0];
		self.type = cqcH[1];
		self.app_id = cqcH[2];

		print("Version: ", self.version);
		print("Type: ", self.type);
		print("App ID: ", self.app_id);
		

