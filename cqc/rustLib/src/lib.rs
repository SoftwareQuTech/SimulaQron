use std::net;
use std::error::Error;

mod error;
use error::CqcError;

pub struct Cqc {
    app_id: u16,
    stream: net::TcpStream,
}

impl Cqc {
    pub fn new(app_id: u16, hostname: &str, portno: u16) -> Result<Cqc, CqcError> {
        let stream = net::TcpStream::connect((hostname, portno))?;
        Ok(Cqc { app_id, stream })
    }

    pub fn simple_cmd(&self, command: u8, qubit_id: u16, notify: u8) {}
    pub fn full_cmd(
        &self,
        command: u8,
        qubit_id: u16,
        notify: char,
        action: char,
        block: char,
        xtra_id: u16,
        steps: u8,
        r_app_id: u16,
        r_node: u32,
        r_port: u16,
        cmdLength: u32,
    ) {
    }

    pub fn hello(&self) {}
    pub fn send(&self, qubit_id: u16, r_app_id: u16, r_node: u32, r_port: u16) {}
    pub fn recv(&self) {}
    pub fn epr(&self, r_app_id: u16, r_node: u32, r_port: u16) {}
    pub fn measure(&self, qubit_id: u16) {}
    pub fn wait_until_done(&self, reps: usize) {}
    pub fn wait_until_newok(&self) {}
    pub fn two_qubit(&self, command: u8, qubit_1_id: u16, qubit_2_id: u16) {}
    pub fn tomography_dir<F>(&self, func: F, iter: u32, dir: u8)
    where
        F: Fn(&Cqc) -> u16,
    {
    }
    pub fn test_qubit<F>(
        &self,
        func: F,
        iter: u32,
        epsilon: f64,
        exp_x: f64,
        exp_y: f64,
        exp_z: f64,
    ) where
        F: Fn(&Cqc) -> u16,
    {
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
