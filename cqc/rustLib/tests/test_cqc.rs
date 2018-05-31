extern crate rust_lib;

use rust_lib::Cqc;
use rust_lib::error::CqcError;
use rust_lib::cqc_api::*;

/*
  Functions purely used for testing purposes, they are called by the
  test_gates.rs
*/

fn cqc_tomography_dir(
    cqc: &Cqc,
    func: &Fn(&Cqc) -> Result<u16, CqcError>,
    n_iter: u32,
    dir: u8,
) -> Result<f64, Box<CqcError>> {
    /**

      cqc_tomography_dir
     
      Obtain tomographic data for a prepared qubit, for testing purposes.
     
      Arguments:
      cqc     an CQC object
      func    function to call to prepare qubit for tomography
      n_iter  number of iterations to perform
      dir     direction to measure (0=Z, 1=X, 2=Y)
     
      Returns:
      ratio   average (in [-1,1] interval).

    **/

    // Translate the direction into a rotation command
    // 0 => Indetity
    // 1 => Hadamard Gate
    // 2 => K-Gate
    let mut cmd: u8;
    match dir {
        0 => {},
        1 => cmd = CQC_CMD_H,
        2 => cmd = CQC_CMD_K,
        _ => println!("Direction can be 0 (Identity), 1 (Hadamard) or 2 (K-Gate).\
                       You have {}.\n \
                       No gate is applied to the qubit in this instance.", dir),
    }

    // Measure in the given direction n_iter times to gather statistics
    let mut count: i32 = 0;
    for i in 0..n_iter {
        // Prepare qubit
        let qubit: u16 = func(cqc).unwrap();

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
    Ok(ratio)
}

pub fn cqc_test_qubit(
    cqc: &Cqc,
    func: &Fn(&Cqc) -> Result<u16, CqcError>,
    n_iter: u32,
    epsilon: f64,
    exp_x: f64,
    exp_y: f64,
    exp_z: f64,
) -> Result<i32, Box<CqcError>> {
    /**
    cqc_test_qubit

    Prepares a qubit according to the indicated function, then performs tomography to verify the preparation up to the indicated precision.

    Arguments:
    cqc	    a CQC object
    func    function to invoke to prepare qubit 
    n_iter  number of times to iterate the test in tomography
    epsilon desired precision
    exp_x   expected value for <X>
    exp_y   expted value for <Y>
    exp_z   expected value for <Z>

    Returns:
    ret     1  for success - state lies in desired interval
            0  for no functional failure but state does not lie in desired interval
            -1 functional error
    **/

    // Run tomography in the X, Y and Z directions
    let tomo_x: f64 = cqc_tomography_dir(cqc, func, n_iter, 1).expect("Tomography x failed.\n");
    let tomo_y: f64 = cqc_tomography_dir(cqc, func, n_iter, 2).expect("Tomography y failed.\n");
    let tomo_z: f64 = cqc_tomography_dir(cqc, func, n_iter, 0).expect("Tomography z failed.\n");

    // Compare to the expected results up to the desired precision.
    // Throw message if precision not met.
    let diff_x = (tomo_x - exp_x).abs();
    let diff_y = (tomo_y - exp_y).abs();
    let diff_z = (tomo_z - exp_z).abs();

    let mut ret = 1;
    if diff_x > epsilon {
        println!("X target precision not met, got {:?} expected {:?}.\n", tomo_x, exp_x);
        ret = 0;
    }
    if diff_y > epsilon {
        println!("Y target precision not met, got {:?} expected {:?}.\n", tomo_y, exp_y);
        ret = 0;
    }
    if diff_z > epsilon {
        println!("Z target precision not met, got {:?} expected {:?}.\n", tomo_z, exp_z);
        ret = 0;
    }

    Ok(ret)
}
