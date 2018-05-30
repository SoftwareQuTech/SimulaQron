extern crate rust_lib;

use rust_lib::Cqc;
use rust_lib::cqc_api::*;
use std::net::Ipv4Addr;

#[test]
fn test_send() {
    // Retrieve arguments from command line
    // These four variables should be read from somewhere else
    let hostname = String::from("localhost");
    let portno: u16 = 8821;
    let remote_host: u32 = u32::from(Ipv4Addr::new(127, 0, 0, 1));
    let remote_port: u16 = 8822;

    // In this example, we are simply application 10
    let app_id: u16 = 10;

    // In this example, we will not check for errors.
    // Initialise a CQC service.
    let cqc = Cqc::new(app_id, &hostname, portno).unwrap();

    cqc.simple_cmd(CQC_CMD_NEW, 0, false).unwrap();
    let qubit = cqc.wait_until_newok().unwrap();

    cqc.send(qubit, app_id, remote_host, remote_port).unwrap();
    cqc.wait_until_done(1).unwrap();
}
