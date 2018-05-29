#[derive(Debug, Serialize, Deserialize)]
pub struct CqcHeader {
    pub version: u8,   // CQC API version.
    pub ctrl_type: u8, // Packet control type.
    pub app_id: u16,   // Application ID.
    pub length: u32,   // Total length of command instructions to send.
}

#[derive(Serialize, Deserialize)]
pub struct CmdHeader {
    pub qubit_id: u16, // Qubit to perform operation on
    pub instr: u8,     // Instruction to execute.
    pub options: u8,   // Options when executing the command.
}

#[derive(Debug, Default, Serialize, Deserialize)]
pub struct XtraCmdHeader {
    pub xtra_qubit_id: u16, // ID of the additional qubit.
    pub r_app_id: u16,      // Remote application ID.
    pub r_node: u32,        // IP of the remote node.
    pub cmd_length: u32,    // Length of the cmds to exectute upon completion.
    pub r_port: u16,        // Port of the remote node for control info.
    pub steps: u8,          // Angle step of rotation (ROT) OR number of repetitions (FACTORY).
    pub unused: u8,         // Need 4 byte segments.
}

#[derive(Debug, Default, Serialize, Deserialize)]
pub struct NotifyHeader {
    pub qubit_id: u16, // ID of the received qubit, if any.
    pub r_app_id: u16, // Remote application ID.
    pub r_node: u32,   // IP of the remote node.
    pub datetime: u64, // Time of qubit.
    pub r_port: u16,   // Port of the remote node for control info.
    pub outcome: u8,   // Measurement outcome.
    pub unused: u8,    // Need 4 byte segments.
}
