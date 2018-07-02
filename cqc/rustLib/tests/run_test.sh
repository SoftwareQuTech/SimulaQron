#!/bin/bash

# Start the Virtual and CQC Nodes
../../../run/startVNodes.sh
../../../run/startCQCNodes.sh

# start the test
cargo test test
cargo test test_gates
cargo test test_send
cargo test test_recv

