extern crate rust_lib;

use rust_lib::Cqc;
use rust_lib::cqc_api::*;
use rust_lib::error::CqcError;

mod test_cqc;
use test_cqc::cqc_test_qubit;

// Prepares a plus state

fn make_plus(cqc: &Cqc) -> Result<u16, CqcError> {
    // Create a new qubit in |0>
    cqc.simple_cmd(CQC_CMD_NEW, 0, false).unwrap();
    let qubit: u16 = cqc.wait_until_newok().unwrap();

    // Turn it into |+>
    cqc.simple_cmd(CQC_CMD_H, qubit, true).unwrap();
    cqc.wait_until_done(1).unwrap();

    Ok(qubit)
}

// Prepares a plus state

fn make_zero(cqc: &Cqc) -> Result<u16, CqcError> {
    // Create a new qubit in |0>
    cqc.simple_cmd(CQC_CMD_NEW, 0, false).unwrap();
    let qubit: u16 = cqc.wait_until_newok().unwrap();

    // Turn it into |+>
    cqc.simple_cmd(CQC_CMD_I, qubit, true).unwrap();
    cqc.wait_until_done(1).unwrap();

    Ok(qubit)
}

// Prepares a y eigenstate

fn make_k(cqc: &Cqc) -> Result<u16, CqcError> {
    // Create a new qubit in |0>
    cqc.simple_cmd(CQC_CMD_NEW, 0, false).unwrap();
    let qubit: u16 = cqc.wait_until_newok().unwrap();

    // Turn it into |+>
    cqc.simple_cmd(CQC_CMD_K, qubit, true).unwrap();
    cqc.wait_until_done(1).unwrap();

    Ok(qubit)
}

#[test]
fn test_gates() {
    // Retrieve arguments from command line
    // These four variables should be read from somewhere else
    let hostname = String::from("localhost");
    let portno: u16 = 8821;

    // In this example, we are simply application 10
    let app_id: u16 = 10;

    // In this example, we will not check for errors.
    // Initialise a CQC service.
    let cqc = Cqc::new(app_id, &hostname, portno).unwrap();

    // Test whether we can make the zero state
    let outcome: i32 = cqc_test_qubit(&cqc, &make_zero, 500, 0.1, 0., 0., 1.).unwrap();

    println!("Testing |0> preparation......................");
    if outcome == 0 {
        println!("fail\n");
    } else {
        println!("ok\n");
    }

    // Test whether we can make the plus state
    let outcome: i32 = cqc_test_qubit(&cqc, &make_plus, 500, 0.1, 1., 0., 0.).unwrap();
    if outcome < 0 {
        println!("Test failed.\n");
    }
    println!("Testing |+> preparation......................");
    if outcome == 0 {
        println!("fail\n");
    } else {
        println!("ok\n");
    }

    // Test whether we can make the y 0 eigenstate
    let outcome: i32 = cqc_test_qubit(&cqc, &make_k, 500, 0.1, 0., 1., 0.).unwrap();
    if outcome < 0 {
        println!("Test failed.\n");
    }
    println!("Testing |1> preparation......................");
    if outcome == 0 {
        println!("fail\n");
    } else {
        println!("ok\n");
    }
}
