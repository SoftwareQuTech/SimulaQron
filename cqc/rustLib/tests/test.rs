extern crate rust_lib;

use rust_lib::Cqc;
use rust_lib::cqc_api::*;

#[test]
fn test_init() {
    // Initialise the host name, port number and application id
    let hostname = String::from("localhost");
    let portno: u16 = 8821;
    let app_id: u16 = 10;

    // Initialise a CQC service
    let cqc = Cqc::new(app_id, &hostname, portno).unwrap();

    // Execute a simple CQC command to create a new qubit
    cqc.simple_cmd(CQC_CMD_NEW, 0, false).unwrap();

    // Get the qubit id
    let qubit = cqc.wait_until_newok().unwrap();

    // Execute a simple CQC command to apply a H-gate to the qubit
    cqc.simple_cmd(CQC_CMD_H, qubit, true).unwrap();

    // Blocking process until H-gate is applied to the qubit
    cqc.wait_until_done(1).unwrap();

    // Blocking measurement of the qubit
    let outcome: u8 = cqc.measure(qubit).unwrap();
    println!("Outcome: {}", outcome);
}
