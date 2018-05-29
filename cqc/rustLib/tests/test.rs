extern crate rustLib;

use rustLib::Cqc;

#[test]
fn test_init() {
    // These four variables should be read from somewhere else
    let hostname = String::from("localhost");
    let portno: u16 = 8821;
    let remote_host = String::from("localhost");
    let remote_port: u16 = 8822;

    // These two values should come from a mastser parameter file
    let cqc_cmd_new = 1;
    let cqc_cmd_h = 17;

    let app_id: u16 = 10;

    // Initialise a CQC service
    let mut cqc = Cqc::new(app_id, &hostname, portno);

    cqc.simple_cmd(cqc_cmd_new, 0, 0);
    let qubit = cqc.wait_until_newok();
    // Cqc.wait_until_newok() should return a qubit_id
    // hard-coded for now to get a qubit_id
    let qubit: u16 = 7;

    //Cqc.simple_cmd(cqc_cmd_h, qubit, 1);
    cqc.simple_cmd(cqc_cmd_h, qubit, 1);
    cqc.wait_until_done(1);

    // hard-coded to get an outcome for now
    //let outcome: u16 = Cqc.measure(qubit);
    let outcome: u16 = 1;
    println!("Outcome: {}", outcome);
}
