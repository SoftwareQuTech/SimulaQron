extern crate bincode;
#[macro_use]
extern crate serde_derive;

use std::net;

use bincode::{deserialize_from, serialize_into};

mod error;
use error::CqcError;

mod cqc_api;
use cqc_api::*;

pub struct Cqc {
    app_id: u16,
    stream: net::TcpStream,
}

impl Cqc {
    pub fn new(app_id: u16, hostname: &str, portno: u16) -> Result<Cqc, CqcError> {
        let stream = net::TcpStream::connect((hostname, portno))?;
        Ok(Cqc { app_id, stream })
    }

    pub fn simple_cmd(&self, command: u8, qubit_id: u16, notify: bool) -> Result<(), CqcError> {
        // Prepare CQC message indicating a command.
        let cqc_header = CqcHeader {
            version: CQC_VERSION,
            ctrl_type: CQC_TP_COMMAND,
            app_id: self.app_id,
            length: CQC_CMD_HDR_LENGTH,
        };

        // Send message to the server.
        serialize_into(&self.stream, &cqc_header)?;

        // Prepare message for the specific command.
        let cmd_header = CmdHeader {
            qubit_id,
            instr: command,
            options: if notify {
                CQC_OPT_NOTIFY | CQC_OPT_BLOCK
            } else {
                0x00
            },
        };

        // Send message to the server.
        serialize_into(&self.stream, &cmd_header)?;

        Ok(())
    }

    pub fn full_cmd(
        &self,
        command: u8,
        qubit_id: u16,
        notify: bool,
        action: bool,
        block: bool,
        xtra_id: u16,
        steps: u8,
        r_app_id: u16,
        r_node: u32,
        r_port: u16,
        cmd_length: u32,
    ) -> Result<(), CqcError> {
        // Prepare a CQC message indicating a command
        let cqc_header = CqcHeader {
            version: CQC_VERSION,
            ctrl_type: CQC_TP_COMMAND,
            app_id: self.app_id,
            length: CQC_CMD_HDR_LENGTH + CQC_CMD_XTRA_LENGTH,
        };

        // Send message to the server.
        serialize_into(&self.stream, &cqc_header)?;

        // Prepare message for the specific command.
        let mut options: u8 = 0;
        if notify {
            options = options | CQC_OPT_NOTIFY;
        }
        if action {
            options = options | CQC_OPT_ACTION;
        }
        if block {
            options = options | CQC_OPT_BLOCK;
        }

        let cmd_header = CmdHeader {
            qubit_id,
            instr: command,
            options,
        };

        // Send message to the server.
        serialize_into(&self.stream, &cmd_header)?;

        // Prepare extra header.
        let xtra_header = XtraCmdHeader {
            xtra_qubit_id: xtra_id,
            steps,
            r_app_id,
            r_node,
            r_port,
            cmd_length,
        };

        // Send message to the server.
        serialize_into(&self.stream, &xtra_header)?;

        Ok(())
    }

    pub fn hello(&self) -> Result<(), CqcError> {
        // Prepare a CQC message indicating a command.
        let cqc_header = CqcHeader {
            version: CQC_VERSION,
            ctrl_type: CQC_TP_HELLO,
            app_id: self.app_id,
            length: CQC_CMD_HDR_LENGTH,
        };

        // Send message to the server.
        serialize_into(&self.stream, &cqc_header)?;

        Ok(())
    }

    pub fn send(
        &self,
        qubit_id: u16,
        r_app_id: u16,
        r_node: u32,
        r_port: u16,
    ) -> Result<(), CqcError> {
        self.full_cmd(
            CQC_CMD_SEND,
            qubit_id,
            true,
            false,
            false,
            0,
            0,
            r_app_id,
            r_node,
            r_port,
            0,
        )
    }

    pub fn recv(&self) -> Result<u16, CqcError> {
        // Send out a request to receive a qubit.
        self.simple_cmd(CQC_CMD_RECV, 0, false)?;

        // Now read CQC header from server response.
        let reply: CqcHeader = deserialize_from(&self.stream)?;

        if reply.ctrl_type != CQC_TP_RECV {
            return Err(CqcError::General);
        }

        // Read qubit id from the notify header.
        let note: NotifyHeader = deserialize_from(&self.stream)?;

        Ok(note.qubit_id)
    }

    pub fn epr(&self, r_app_id: u16, r_node: u32, r_port: u16) -> Result<(), CqcError> {
        self.full_cmd(
            CQC_CMD_RECV,
            0,
            false,
            false,
            true,
            0,
            0,
            r_app_id,
            r_node,
            r_port,
            0,
        )
    }

    pub fn measure(&self, qubit_id: u16) -> Result<u8, CqcError> {
        // Send a CQC message to request measurement.
        self.simple_cmd(CQC_CMD_MEASURE, qubit_id, false)?;

        // Read the response.
        let reply: CqcHeader = deserialize_from(&self.stream)?;

        if reply.ctrl_type != CQC_TP_MEASOUT {
            return Err(CqcError::General);
        }

        // Read measurement outcome.
        let note: NotifyHeader = deserialize_from(&self.stream)?;

        Ok(note.outcome)
    }

    pub fn wait_until_done(&self, reps: usize) -> Result<(), CqcError> {
        // Read the CQC header from the server response.
        for _ in 0..reps {
            let reply: CqcHeader = deserialize_from(&self.stream)?;

            if reply.ctrl_type >= CQC_ERR_GENERAL || reply.ctrl_type != CQC_TP_DONE {
                return Err(CqcError::General);
            }
        }

        Ok(())
    }

    pub fn wait_until_newok(&self) -> Result<u16, CqcError> {
        // Read the CQC header from the server response.
        let reply: CqcHeader = deserialize_from(&self.stream)?;

        if reply.ctrl_type >= CQC_ERR_GENERAL || reply.ctrl_type != CQC_TP_NEW_OK {
            return Err(CqcError::General);
        }

        // Read the qubit id.
        let note: NotifyHeader = deserialize_from(&self.stream)?;

        Ok(note.qubit_id)
    }

    pub fn two_qubit(&self, command: u8, qubit_1_id: u16, qubit_2_id: u16) -> Result<(), CqcError> {
        self.full_cmd(
            command,
            qubit_1_id,
            false,
            false,
            true,
            qubit_2_id,
            0,
            0,
            0,
            0,
            0,
        )
    }
}

impl Drop for Cqc {
    fn drop(&mut self) {
        let _ = self.stream.shutdown(net::Shutdown::Both);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cqc_init() -> Cqc {
        match Cqc::new(10, "localhost", 8821) {
            Ok(cqc) => cqc,
            Err(CqcError::Io(ref io_err)) => {
                println!("{}", io_err);
                panic!();
            }
            _ => panic!(),
        }
    }

    #[test]
    fn connect() {
        let cqc = cqc_init();
    }
}
