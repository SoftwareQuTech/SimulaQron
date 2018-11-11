extern crate cqc;
extern crate rust_lib;

use cqc::hdr;
use rust_lib::Cqc;

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
fn cqc_tomography_dir(cqc: &mut Cqc, func: &Fn(&mut Cqc) -> u16, n_iter: u32, dir: u8) -> f64 {
    // Measure in the given direction n_iter times to gather statistics
    let mut count: i32 = 0;
    for _ in 0..n_iter {
        // Prepare qubit
        let qubit: u16 = func(cqc);

        // Apply the rotation
        if dir > 0 {
            let options = *hdr::CmdOpt::empty().set_notify().set_block();
            let request = match dir {
                1 => cqc.builder.cmd_h(qubit, options),
                2 => cqc.builder.cmd_k(qubit, options),
                _ => panic!(
                    "Direction can be 1 (Hadamard) or 2 (K-Gate).\
                     You have {}.\n \
                     No gate is applied to the qubit in this instance.",
                    dir
                ),
            };
            cqc.encode_and_send(&request).unwrap();
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
// conf    confidence region (acceptable error is +/- conf/sqrt(n_iter))
// exp_x   expected value for <X>
// exp_y   expted value for <Y>
// exp_z   expected value for <Z>
fn cqc_test_qubit(
    cqc: &mut Cqc,
    func: &Fn(&mut Cqc) -> u16,
    n_iter: u32,
    conf: u32,
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

    // Define the acceptable tolerance to be conf/
    let epsilon: f64 = (conf as f64) / (n_iter as f64).sqrt();

    assert!(
        diff_x <= epsilon,
        format!(
            "X target precision not met, got {:?} expected {:?}.\n",
            tomo_x, exp_x
        )
    );
    assert!(
        diff_y <= epsilon,
        format!(
            "Y target precision not met, got {:?} expected {:?}.\n",
            tomo_y, exp_y
        )
    );
    assert!(
        diff_z <= epsilon,
        format!(
            "Z target precision not met, got {:?} expected {:?}.\n",
            tomo_z, exp_z
        )
    );
}

// Prepares a plus state
fn make_plus(cqc: &mut Cqc) -> u16 {
    // Create a new qubit in |0>
    let request = cqc.builder.cmd_new(0, hdr::CmdOpt::empty());
    cqc.encode_and_send(&request).unwrap();
    let qubit: u16 = cqc.wait_until_newok().unwrap();

    // Turn it into |+>
    let request = cqc.builder.cmd_h(
        qubit,
        *hdr::CmdOpt::empty().set_notify().set_block(),
    );
    cqc.encode_and_send(&request).unwrap();
    cqc.wait_until_done(1).unwrap();

    qubit
}

// Prepares a zero state
fn make_zero(cqc: &mut Cqc) -> u16 {
    // Create a new qubit in |0>
    let request = cqc.builder.cmd_new(0, hdr::CmdOpt::empty());
    cqc.encode_and_send(&request).unwrap();
    let qubit: u16 = cqc.wait_until_newok().unwrap();

    qubit
}

// Prepares a y_0 eigenstate
fn make_k(cqc: &mut Cqc) -> u16 {
    // Create a new qubit in |0>
    let request = cqc.builder.cmd_new(0, hdr::CmdOpt::empty());
    cqc.encode_and_send(&request).unwrap();
    let qubit: u16 = cqc.wait_until_newok().unwrap();

    // Turn it into |+>
    let request = cqc.builder.cmd_k(
        qubit,
        *hdr::CmdOpt::empty().set_notify().set_block(),
    );
    cqc.encode_and_send(&request).unwrap();
    cqc.wait_until_done(1).unwrap();

    qubit
}

#[test]
fn test_gates() {
    // Initialise the host name, port number and application id
    let hostname = String::from("localhost");
    let portno: u16 = 8803;
    let app_id: u16 = 10;
    let n_iter = 100;
    let conf = 2;

    // In this example, we will not check for errors.
    // Initialise a CQC service.
    let mut cqc = Cqc::new(app_id, &hostname, portno).unwrap();

    // Test whether we can make the zero state
    println!("Testing z-basis preparation: |0>");
    cqc_test_qubit(&mut cqc, &make_zero, n_iter, conf, 0., 0., 1.);

    // Test whether we can make the plus state
    println!("Testing x-basis preparation: |0>+|1>");
    cqc_test_qubit(&mut cqc, &make_plus, n_iter, conf, 1., 0., 0.);

    // Test whether we can make the y_0 eigenstate
    println!("Testing y-basis preparation: |0>+i|1>");
    cqc_test_qubit(&mut cqc, &make_k, n_iter, conf, 0., 1., 0.);
}
