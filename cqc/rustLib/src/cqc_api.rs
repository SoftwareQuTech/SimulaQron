#![allow(dead_code)]

// Basic CQC Header format.
pub const CQC_HDR_LENGTH: u32 = 8;

#[derive(Serialize, Deserialize)]
pub struct CqcHeader {
    pub version: u8,   // CQC API version.
    pub ctrl_type: u8, // Packet control type.
    pub app_id: u16,   // Application ID.
    pub length: u32,   // Total length of command instructions to send.
}

// CQC Version.
pub const CQC_VERSION: u8 = 0;

// Possible CQC types.
pub const CQC_TP_HELLO: u8 = 0; // Alive check.
pub const CQC_TP_COMMAND: u8 = 1; // Execute a command list.
pub const CQC_TP_FACTORY: u8 = 2; // Start executing command list repeatedly.
pub const CQC_TP_EXPIRE: u8 = 3; // Qubit has expired.
pub const CQC_TP_DONE: u8 = 4; // Command execution done.
pub const CQC_TP_RECV: u8 = 5; // Recevied qubit.
pub const CQC_TP_EPR_OK: u8 = 6; // Created EPR pair.
pub const CQC_TP_MEASOUT: u8 = 7; // Measurement outcome.
pub const CQC_TP_GET_TIME: u8 = 8; // Get creation time of qubit.
pub const CQC_TP_INF_TIME: u8 = 9; // Inform about time.
pub const CQC_TP_NEW_OK: u8 = 10; // Created new qubit.

pub const CQC_ERR_GENERAL: u8 = 20; // General purpose error no details.
pub const CQC_ERR_NOQUBIT: u8 = 21; // No more qubits available.
pub const CQC_ERR_UNSUPP: u8 = 22; // Command sequence not supported.
pub const CQC_ERR_TIMEOUT: u8 = 23; // Timeout.

// Definition for the command header and commands.
pub const CQC_CMD_HDR_LENGTH: u32 = 4;

#[derive(Serialize, Deserialize)]
pub struct CmdHeader {
    pub qubit_id: u16, // Qubit to perform operation on
    pub instr: u8,     // Instruction to execute.
    pub options: u8,   // Options when executing the command.
}

// Possible commands.
pub const CQC_CMD_I: u8 = 0; // Identity (do nothing, wait one step).
pub const CQC_CMD_NEW: u8 = 1; // Ask for a new qubit.
pub const CQC_CMD_MEASURE: u8 = 2; // Measure qubit.
pub const CQC_CMD_MEASURE_INPLACE: u8 = 3; // Measure qubit inplace.
pub const CQC_CMD_RESET: u8 = 4; // Reset qubit to |0>.
pub const CQC_CMD_SEND: u8 = 5; // Send qubit to another node.
pub const CQC_CMD_RECV: u8 = 6; // Ask to receive qubit.
pub const CQC_CMD_EPR: u8 = 7; // Create EPR pair with the specified node.
pub const CQC_CMD_EPR_RECV: u8 = 8; // Receive EPR pair.

pub const CQC_CMD_X: u8 = 10; // Pauli X.
pub const CQC_CMD_Z: u8 = 11; // Pauli Z.
pub const CQC_CMD_Y: u8 = 12; // Pauli Y.
pub const CQC_CMD_T: u8 = 13; // T Gate.
pub const CQC_CMD_ROT_X: u8 = 14; // Rotation over angle around X in pi/256 increments.
pub const CQC_CMD_ROT_Y: u8 = 15; // Rotation over angle around Y in pi/256 increments.
pub const CQC_CMD_ROT_Z: u8 = 16; // Rotation over angle around Z in pi/256 increments.
pub const CQC_CMD_H: u8 = 17; // Hadamard Gate.
pub const CQC_CMD_K: u8 = 18; // K Gate - taking computational to Y eigenbasis.

pub const CQC_CMD_CNOT: u8 = 20; // CNOT Gate with this as control.
pub const CQC_CMD_CPHASE: u8 = 21; // CPHASE Gate with this as control.

// Command options
pub const CQC_OPT_NOTIFY: u8 = 0x01; // Send a notification when cmd done.
pub const CQC_OPT_ACTION: u8 = 0x02; // On if there are actions to execute when done.
pub const CQC_OPT_BLOCK: u8 = 0x04; // Block until command is done.
pub const CQC_OPT_IFTHEN: u8 = 0x08; // Execute commands depending on outcome.

// Additional cmd details (optional)
pub const CQC_CMD_XTRA_LENGTH: u32 = 16;

#[derive(Serialize, Deserialize)]
pub struct XtraCmdHeader {
    pub xtra_qubit_id: u16, // ID of the additional qubit.
    pub r_app_id: u16,      // Remote application ID.
    pub r_node: u32,        // IP of the remote node.
    pub cmd_length: u32,    // Length of the cmds to exectute upon completion.
    pub r_port: u16,        // Port of the remote node for control info.
    pub steps: u8,          // Angle step of rotation (ROT) OR number of repetitions (FACTORY).
}

// Definitions for the packet sent upon notifications.
pub const CQC_NOTIFY_LENGTH: u32 = 20;

#[derive(Serialize, Deserialize)]
pub struct NotifyHeader {
    pub qubit_id: u16,
    pub r_app_id: u16,
    pub r_node: u32,
    pub datetime: u64,
    pub r_port: u16,
    pub outcome: u8,
}
