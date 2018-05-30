extern crate rust_lib;

use rust_lib::Cqc;

#[test]
fn test_recv() {
    // Retrieve arguments from command line
    // These four variables should be read from somewhere else
    let hostname = String::from("localhost");
    let portno: u16 = 8821;

    // In this example, we are simply application 10
    let app_id: u16 = 10;

    // In this example, we will not check for errors.
    // Initialise a CQC service.
    let cqc = Cqc::new(app_id, &hostname, portno).unwrap();

    let qubit: u16 = cqc.recv().unwrap();
    println!("The qubit receoved is {:?}", qubit);
}
