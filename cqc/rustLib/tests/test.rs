extern crate rustLib;

use rustLib::Cqc;

#[test]
fn main() {
    let hostname = String::from("localhost");
    let portno: u16 = 8821;
    let remote_host = String::from("localhost");
    let remote_port: u16 = 8822;
    let argc = 5;

    // These two values should come from a mastser parameter file
    let cqc_cmd_new = 1;
    let cqc_cmd_h = 17;

    // Retrieve arguments from command line
    if argc != 5 {
        println!("Require: hostname port remoteHost remotePort\n");
        println!("{} arguments are provided.\n", argc-1);
    }

    let app_id: u16 = 10;

    let mut cqc = Cqc::new(app_id);

    cqc.connect(&hostname, portno);

    cqc.simple_cmd(cqc_cmd_new, 0, 0);
    let qubit = cqc.wait_until_newok();
    // Cqc.wait_until_newok() should return a qubit_id
    // hard-coded for now to get a qubit_id
    let qubit_id: u16 = 7;

    //Cqc.simple_cmd(CQC_CMD_H, qubit, 1);
    cqc.simple_cmd(cqc_cmd_h, qubit_id, 1);
    cqc.wait_until_done(1);

    // hard-coded to get an outcome for now
    //let outcome: u16 = Cqc.measure(qubit);
    let outcome: u16 = 1;
    println!("Outcome: {}", outcome);
}
