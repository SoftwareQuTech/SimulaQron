extern crate rust_lib;

use rust_lib::Cqc;
use rust_lib::cqc_api::*;

// cqc_tomography_dir
//
// Obtain tomographic data for a prepared qubit, for testing purposes.
//
// Arguments:
// cqc     an CQC object
// func    function to call to prepare qubit for tomography
// n_iter  number of iterations to perform
// dir     direction to measure (0=Z, 1=X, 2=Y)
//
// Returns:
// ratio   average (in [-1,1] interval).
fn cqc_tomography_dir(
    cqc: &Cqc,
    func: &Fn(&Cqc) -> u16,
    n_iter: u32,
    dir: u8,
) -> f64 {

    // Translate the direction into a rotation command
    // 0 => Indetity
    // 1 => Hadamard Gate
    // 2 => K-Gate
    let mut cmd: u8 = CQC_CMD_I;
    match dir {
        0 => {},
        1 => cmd = CQC_CMD_H,
        2 => cmd = CQC_CMD_K,
        _ => panic!("Direction can be 0 (Identity), 1 (Hadamard) or 2 (K-Gate).\
                     You have {}.\n \
                     No gate is applied to the qubit in this instance.", dir),
    }

    // Measure in the given direction n_iter times to gather statistics
    let mut count: i32 = 0;
    for _ in 0..n_iter {
        // Prepare qubit
        let qubit: u16 = func(cqc);

        // Apply the rotation
        if dir > 0 {
            cqc.simple_cmd(cmd, qubit, true).unwrap();
            cqc.wait_until_done(1).unwrap();
        }

        // Measure in the indicated direction
        let outcome: u8 = cqc.measure(qubit).unwrap();

        // Add to the total count: note outcome needs to be +/-1 for 0/1 to yield expectations
        if outcome == 0 {
            count += 1;
        } else {
            count -= 1;
        }
    }

    let ratio: f64 = (count as f64) / (n_iter as f64);
    ratio
}

// cqc_test_qubit
//
// Prepares a qubit according to the indicated function, then performs
// tomography to verify the preparation up to the indicated precision.
//
// Arguments:
// cqc	    a CQC object
// func    function to invoke to prepare qubit
// n_iter  number of times to iterate the test in tomography
// epsilon desired precision
// exp_x   expected value for <X>
// exp_y   expted value for <Y>
// exp_z   expected value for <Z>
fn cqc_test_qubit(
    cqc: &Cqc,
    func: &Fn(&Cqc) -> u16,
    n_iter: u32,
    epsilon: f64,
    exp_x: f64,
    exp_y: f64,
    exp_z: f64,
) {
    // Run tomography in the X, Y and Z directions
    let tomo_x: f64 = cqc_tomography_dir(cqc, func, n_iter, 1);
    let tomo_y: f64 = cqc_tomography_dir(cqc, func, n_iter, 2);
    let tomo_z: f64 = cqc_tomography_dir(cqc, func, n_iter, 0);

    // Compare to the expected results up to the desired precision.
    // Throw message if precision not met.
    let diff_x = (tomo_x - exp_x).abs();
    let diff_y = (tomo_y - exp_y).abs();
    let diff_z = (tomo_z - exp_z).abs();

    assert!(diff_x <= epsilon,
            format!("X target precision not met, got {:?} expected {:?}.\n", tomo_x, exp_x));
    assert!(diff_y <= epsilon,
            format!("Y target precision not met, got {:?} expected {:?}.\n", tomo_y, exp_y));
    assert!(diff_z <= epsilon,
            format!("Z target precision not met, got {:?} expected {:?}.\n", tomo_z, exp_z));
}

// Prepares a plus state
fn make_plus(cqc: &Cqc) -> u16 {
    // Create a new qubit in |0>
    cqc.simple_cmd(CQC_CMD_NEW, 0, false).unwrap();
    let qubit: u16 = cqc.wait_until_newok().unwrap();

    // Turn it into |+>
    cqc.simple_cmd(CQC_CMD_H, qubit, true).unwrap();
    cqc.wait_until_done(1).unwrap();

    qubit
}

// Prepares a zero state
fn make_zero(cqc: &Cqc) -> u16 {
    // Create a new qubit in |0>
    cqc.simple_cmd(CQC_CMD_NEW, 0, false).unwrap();
    let qubit: u16 = cqc.wait_until_newok().unwrap();

    // Keep it as |0>
    cqc.simple_cmd(CQC_CMD_I, qubit, true).unwrap();
    cqc.wait_until_done(1).unwrap();

    qubit
}

// Prepares a y_0 eigenstate
fn make_k(cqc: &Cqc) -> u16 {
    // Create a new qubit in |0>
    cqc.simple_cmd(CQC_CMD_NEW, 0, false).unwrap();
    let qubit: u16 = cqc.wait_until_newok().unwrap();

    // Turn it into |+>
    cqc.simple_cmd(CQC_CMD_K, qubit, true).unwrap();
    cqc.wait_until_done(1).unwrap();

    qubit
}

#[test]
fn test_gates() {
    // Initialise the host name, port number and application id
    let hostname = String::from("localhost");
    let portno: u16 = 8821;
    let app_id: u16 = 10;

    // In this example, we will not check for errors.
    // Initialise a CQC service.
    let cqc = Cqc::new(app_id, &hostname, portno).unwrap();

    // Test whether we can make the zero state
    println!("Testing |0> preparation......................");
    cqc_test_qubit(&cqc, &make_zero, 500, 0.1, 0., 0., 1.);

    // Test whether we can make the plus state
    println!("Testing |+> preparation......................");
    cqc_test_qubit(&cqc, &make_plus, 500, 0.1, 1., 0., 0.);

    // Test whether we can make the y_0 eigenstate
    println!("Testing |1> preparation......................");
    cqc_test_qubit(&cqc, &make_k, 500, 0.1, 0., 1., 0.);

}
