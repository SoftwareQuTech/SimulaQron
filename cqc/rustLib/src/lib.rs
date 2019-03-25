extern crate bincode;
extern crate cqc;

use cqc::builder;
use cqc::hdr;
use std::error::Error;
use std::io;
use std::net;

pub struct Cqc {
    pub builder: builder::Builder,
    stream: net::TcpStream,
    coder: bincode::Config,
}

impl Cqc {
    pub fn new(app_id: u16, hostname: &str, portno: u16) -> Result<Cqc, io::Error> {
        let builder = builder::Builder::new(app_id);
        let stream = net::TcpStream::connect((hostname, portno))?;
        let mut coder = bincode::config();
        coder.big_endian();
        Ok(Cqc {
            builder,
            stream,
            coder,
        })
    }

    pub fn encode_and_send(&self, request: &cqc::Request) -> Result<(), Box<Error>> {
        Ok(self.coder.serialize_into(&self.stream, request)?)
    }

    pub fn receive_and_decode(&self) -> Result<cqc::Response, Box<Error>> {
        Ok(self.coder.deserialize_from(&self.stream)?)
    }

    pub fn hello(&self) -> Result<(), Box<Error>> {
        self.encode_and_send(&self.builder.hello())
    }

    pub fn send(
        &self,
        qubit_id: u16,
        remote_app_id: u16,
        remote_node: u32,
        remote_port: u16,
    ) -> Result<(), Box<Error>> {
        let request = self.builder.cmd_send(
            qubit_id,
            *hdr::CmdOpt::empty().set_notify(),
            builder::RemoteId {
                remote_app_id,
                remote_node,
                remote_port,
            },
        );
        self.encode_and_send(&request)
    }

    pub fn recv(&mut self) -> Result<u16, Box<Error>> {
        // Send out a request to receive a qubit.
        self.encode_and_send(
            &self.builder.cmd_recv(0, hdr::CmdOpt::empty()),
        )?;

        // Now read CQC header from server response.
        let response = self.receive_and_decode()?;

        // Check if the return type is correct.
        if !response.cqc_hdr.msg_type.is_recv() {
            return Err(From::from("Unexpected response"));
        }

        // Extract the Qubit header.
        if !response.notify.is_qubit_hdr() {
            return Err(From::from("Unexpected response"));
        }
        let note = response.notify.get_qubit_hdr();

        Ok(note.qubit_id)
    }

    pub fn measure(&mut self, qubit_id: u16) -> Result<u8, Box<Error>> {
        // Send a CQC message to request measurement.
        self.encode_and_send(&self.builder.cmd_measure(
            qubit_id,
            hdr::CmdOpt::empty(),
        ))?;

        // Now read the response.
        let response = self.receive_and_decode()?;

        // Check if the return type is correct.
        if !response.cqc_hdr.msg_type.is_measout() {
            return Err(From::from(format!("Unexpected response")));
        }

        // Extract the Notify header.
        if !response.notify.is_meas_out_hdr() {
            return Err(From::from("Unexpected response"));
        }
        let note = response.notify.get_meas_out_hdr();

        Ok(note.meas_out as u8)
    }

    pub fn wait_until_done(&mut self, reps: usize) -> Result<(), Box<Error>> {
        for _ in 0..reps {
            let response = self.receive_and_decode()?;
            if !response.cqc_hdr.msg_type.is_done() {
                return Err(From::from(format!("Unexpected response")));
            }
        }
        Ok(())
    }

    pub fn wait_until_newok(&mut self) -> Result<u16, Box<Error>> {
        let response = self.receive_and_decode()?;

        // Check if the return type is correct.
        if !response.cqc_hdr.msg_type.is_new_ok() {
            return Err(From::from(format!("Unexpected response")));
        }

        // Extract the Notify header.
        if !response.notify.is_qubit_hdr() {
            return Err(From::from("Unexpected response"));
        }
        let note = response.notify.get_qubit_hdr();

        Ok(note.qubit_id)
    }
}
