extern crate rust_lib;

use rust_lib::Cqc;
use rust_lib::error::CqcError;
use rust_lib::cqc_api::*;

fn cqc_tomography_dir(
    cqc: &Cqc,
    func: &Fn(&Cqc) -> Result<u16, CqcError>,
    iteration: u32,
    dir: u8,
) -> Result<f64, Box<CqcError>> {
    // Translate the direction into a rotation command
    let mut cmd: u8 = 0;
    match dir {
        0 => cmd = CQC_CMD_I,
        1 => cmd = CQC_CMD_H,
        2 => cmd = CQC_CMD_K,
        _ => println!("Direction can be either 0, 1 or 2. You have {}.\n", dir),
    }

    // Measure in the given direction iter times to gather stats
    let mut count: i32 = 0;
    for i in 0..iteration {
        // Prepare qubit
        let qubit: u16 = func(cqc).unwrap();

        // Measure in the indicated direction
        if dir > 0 {
            cqc.simple_cmd(cmd, qubit, true).unwrap();
            cqc.wait_until_done(1).unwrap();
        }

        let outcome: u8 = cqc.measure(qubit).unwrap();
        //let outcome: i32 = 1;
        if outcome < 0 {
            panic!("Tomography measurement failed for qubit {:?}.\n", qubit);
        }

        // Add to the total count: note outcome needs to be +/-1 for 0/1 to yield expectations
        if outcome == 0 {
            count += 1;
        } else {
            count -= 1;
        }
    }

    let ratio: f64 = (count as f64) / (iteration as f64);
    Ok(ratio)
}

pub fn cqc_test_qubit(
    cqc: &Cqc,
    func: &Fn(&Cqc) -> Result<u16, CqcError>,
    iteration: u32,
    epsilon: f64,
    exp_x: f64,
    exp_y: f64,
    exp_z: f64,
) -> Result<i32, Box<CqcError>> {
    /*
    cqc_test_qubit

    Prepares a qubit according to the indicated function, then performs tomography to verify the preparation up to the indicated precision.

    Arguments
    cqc		cqc connection
    func		function to invoke to prepare qubit 
    iter		number of times to iterate the test in tomography
    epsilon	desired precision
    exp_x	expected value for <X>
    exp_y	expted value for <Y>
    exp_z	expected value for <Z>

    Returns
    1  for success - state lies in desired interval
    0  for no functional failure but state does not lie in desired interval
    -1 functional error
    */

    // Run tomography in X, Z and Y directions
    let tomo_z: f64 = cqc_tomography_dir(cqc, func, iteration, 0).expect("Tomography z failed.\n");
    let tomo_x: f64 = cqc_tomography_dir(cqc, func, iteration, 1).expect("Tomography x failed.\n");
    let tomo_y: f64 = cqc_tomography_dir(cqc, func, iteration, 2).expect("Tomography y failed.\n");

    // Compare to the expected results up to the desired precision
    let diff_x = (tomo_x - exp_x).abs();
    let diff_y = (tomo_y - exp_y).abs();
    let diff_z = (tomo_z - exp_z).abs();

    let mut ret = 1;
    if diff_x > epsilon {
        println!("X target not met, got {:?} expected {:?}.\n", tomo_x, exp_x);
        ret = 0;
    }
    if diff_z > epsilon {
        println!("Z target not met, got {:?} expected {:?}.\n", tomo_z, exp_z);
        ret = 0;
    }
    if diff_y > epsilon {
        println!("Y target not met, got {:?} expected {:?}.\n", tomo_y, exp_y);
        ret = 0;
    }

    Ok(ret)
}
