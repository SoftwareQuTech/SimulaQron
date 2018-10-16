extern crate cqc;
extern crate rust_lib;

use cqc::hdr;
use rust_lib::Cqc;

#[test]
fn test_init() {
    // Initialise the host name, port number and application id
    let hostname = String::from("localhost");
    let portno: u16 = 8803;
    let app_id: u16 = 10;

    // Initialise a CQC service
    let mut cqc = Cqc::new(app_id, &hostname, portno).unwrap();

    // Execute a simple CQC command to create a new qubit
    let request = cqc.builder.cmd_new(0, hdr::CmdOpt::empty());
    cqc.encode_and_send(&request).unwrap();

    // Get the qubit id
    let qubit = cqc.wait_until_newok().unwrap();

    // Execute a simple CQC command to apply a H-gate to the qubit
    let request = cqc.builder.cmd_h(
        qubit,
        *hdr::CmdOpt::empty().set_notify().set_block(),
    );
    cqc.encode_and_send(&request).unwrap();

    // Blocking process until H-gate is applied to the qubit
    cqc.wait_until_done(1).unwrap();

    // Blocking measurement of the qubit
    let outcome: u8 = cqc.measure(qubit).unwrap();
    println!("Outcome: {}", outcome);
}
