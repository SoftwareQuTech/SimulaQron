extern crate rust_lib;

use rust_lib::Cqc;

#[test]
fn test_recv() {
    // Initialise the host name, port number and application id
    let hostname = String::from("localhost");
    let portno: u16 = 8822;
    let app_id: u16 = 10;

    // In this example, we will not check for errors.
    // Initialise a CQC service.
    let cqc = Cqc::new(app_id, &hostname, portno).unwrap();

    // Receive qubit from any source
    let qubit: u16 = cqc.recv().unwrap();
    println!("The qubit receoved is {:?}", qubit);
}
