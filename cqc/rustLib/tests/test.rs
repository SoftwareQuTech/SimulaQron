extern crate rust_lib;

use rust_lib::Cqc;
use rust_lib::cqc_api::*;

#[test]
fn test_init() {
    // These four variables should be read from somewhere else
    let hostname = String::from("localhost");
    let portno: u16 = 8821;

    let app_id: u16 = 10;

    // Initialise a CQC service
    let cqc = Cqc::new(app_id, &hostname, portno).unwrap();

    cqc.simple_cmd(CQC_CMD_NEW, 0, false).unwrap();
    let qubit = cqc.wait_until_newok().unwrap();

    //Cqc.simple_cmd(cqc_cmd_h, qubit, 1);
    cqc.simple_cmd(CQC_CMD_H, qubit, true).unwrap();
    cqc.wait_until_done(1).unwrap();

    // hard-coded to get an outcome for now
    let outcome: u8 = cqc.measure(qubit).unwrap();
    println!("Outcome: {}", outcome);
}
