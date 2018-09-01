extern crate cqc;

use cqc::decode;
use cqc::encode;
use cqc::hdr;
use cqc::hdr::CmdOpt;
use cqc::Request;
use std::error::Error;
use std::io;
use std::io::{Read, Write};
use std::net;

pub struct Cqc {
    app_id: u16,
    stream: net::TcpStream,
    encoder: encode::Encoder,
    decoder: decode::Decoder,
}

impl Cqc {
    pub fn new(app_id: u16, hostname: &str, portno: u16) -> Result<Cqc, io::Error> {
        let stream = net::TcpStream::connect((hostname, portno))?;
        let encoder = encode::Encoder::new();
        let decoder = decode::Decoder::new();
        Ok(Cqc {
            app_id,
            stream,
            encoder,
            decoder,
        })
    }

    fn encode_and_send(&mut self, request: &cqc::Request) -> Result<(), io::Error> {
        let buf_len = encode::Encoder::encode_request_len(&request);
        let mut buffer = vec![0; buf_len];
        self.encoder.encode_request(&request, &mut buffer);

        self.stream.write(&buffer)?;

        Ok(())
    }

    pub fn simple_cmd(
        &mut self,
        command: u8,
        qubit_id: u16,
        notify: bool,
    ) -> Result<(), io::Error> {
        let options = if notify {
            CmdOpt::NOTIFY | CmdOpt::BLOCK
        } else {
            CmdOpt::empty()
        };

        let cmd = hdr::Cmd::get_cmd(command).unwrap();

        let mut request = Request::command(self.app_id);
        request.build_req_cmd(qubit_id, cmd, options, None);

        self.encode_and_send(&request)
    }

    pub fn full_cmd(
        &mut self,
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
    ) -> Result<(), io::Error> {
        let mut options = CmdOpt::empty();
        if notify {
            options.set_notify();
        }
        if action {
            options.set_action();
        }
        if block {
            options.set_block();
        }

        let xtra_hdr = hdr::XtraHdr {
            xtra_qubit_id: xtra_id,
            remote_app_id: r_app_id,
            remote_node: r_node,
            cmd_length: cmd_length,
            remote_port: r_port,
            steps: steps,
            align: 0,
        };

        let cmd = hdr::Cmd::get_cmd(command).unwrap();

        let mut request = Request::command(self.app_id);
        request.build_req_cmd(qubit_id, cmd, options, Some(xtra_hdr));

        self.encode_and_send(&request)
    }

    pub fn hello(&mut self) -> Result<(), io::Error> {
        let request = Request::hello(self.app_id);
        self.encode_and_send(&request)
    }

    pub fn send(
        &mut self,
        qubit_id: u16,
        r_app_id: u16,
        r_node: u32,
        r_port: u16,
    ) -> Result<(), io::Error> {
        self.full_cmd(
            hdr::Cmd::Send as u8,
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

    pub fn recv(&mut self) -> Result<u16, Box<Error>> {
        // Send out a request to receive a qubit.
        self.simple_cmd(hdr::Cmd::Recv as u8, 0, false)?;

        // Prepare a buffer for a receive of a CQC and Notify headers.
        let buf_len: usize = (hdr::CQC_HDR_LENGTH + hdr::NOTIFY_HDR_LENGTH) as usize;
        let mut buffer = vec![0; buf_len];

        // Now read CQC header from server response.
        self.stream.read(&mut buffer[..])?;
        let (_, status) = self.decoder.decode(&buffer)?;
        let response = status.unwrap().get_response().unwrap();

        // Check if the return type is correct.
        if !response.cqc_hdr.msg_type.is_recv() {
            return Err(From::from(format!("Unexpected response")));
        }

        // Extract the Notify header.
        let note = response.notify.unwrap().get_notify_hdr().unwrap();

        Ok(note.qubit_id)
    }

    pub fn epr(&mut self, r_app_id: u16, r_node: u32, r_port: u16) -> Result<(), io::Error> {
        self.full_cmd(
            hdr::Cmd::Recv as u8,
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

    pub fn measure(&mut self, qubit_id: u16) -> Result<u8, Box<Error>> {
        // Send a CQC message to request measurement.
        self.simple_cmd(hdr::Cmd::Measure as u8, qubit_id, false)?;

        // Prepare a buffer for a receive of a CQC and Notify headers.
        let buf_len: usize = (hdr::CQC_HDR_LENGTH + hdr::NOTIFY_HDR_LENGTH) as usize;
        let mut buffer = vec![0; buf_len];

        // Now read the response.
        self.stream.read(&mut buffer[..])?;
        let (_, status) = self.decoder.decode(&buffer)?;
        let response = status.unwrap().get_response().unwrap();

        // Check if the return type is correct.
        if !response.cqc_hdr.msg_type.is_measout() {
            return Err(From::from(format!("Unexpected response")));
        }

        // Extract the Notify header.
        let note = response.notify.unwrap().get_notify_hdr().unwrap();

        Ok(note.outcome)
    }

    pub fn wait_until_done(&mut self, reps: usize) -> Result<(), Box<Error>> {
        // Prepare a buffer for a receive of a CQC and Notify headers.
        let buf_len: usize = hdr::CQC_HDR_LENGTH as usize;
        let mut buffer = vec![0; buf_len];

        for _ in 0..reps {
            self.stream.read(&mut buffer[..])?;
            let (_, status) = self.decoder.decode(&buffer)?;
            let response = status.unwrap().get_response().unwrap();

            if !response.cqc_hdr.msg_type.is_done() {
                return Err(From::from(format!("Unexpected response")));
            }
        }

        Ok(())
    }

    pub fn wait_until_newok(&mut self) -> Result<u16, Box<Error>> {
        // Prepare a buffer for a receive of a CQC and Notify headers.
        let buf_len: usize = (hdr::CQC_HDR_LENGTH + hdr::NOTIFY_HDR_LENGTH) as usize;
        let mut buffer = vec![0; buf_len];

        // Now read CQC header from server response.
        self.stream.read(&mut buffer[..])?;
        let (_, status) = self.decoder.decode(&buffer)?;
        let response = status.unwrap().get_response().unwrap();

        // Check if the return type is correct.
        if !response.cqc_hdr.msg_type.is_new_ok() {
            return Err(From::from(format!("Unexpected response")));
        }

        // Extract the Notify header.
        let note = response.notify.unwrap().get_notify_hdr().unwrap();

        Ok(note.qubit_id)
    }

    pub fn two_qubit(
        &mut self,
        command: u8,
        qubit_1_id: u16,
        qubit_2_id: u16,
    ) -> Result<(), io::Error> {
        self.full_cmd(
            command, qubit_1_id, false, false, true, qubit_2_id, 0, 0, 0, 0, 0,
        )
    }
}

impl Drop for Cqc {
    fn drop(&mut self) {
        let _ = self.stream.shutdown(net::Shutdown::Both);
    }
}
