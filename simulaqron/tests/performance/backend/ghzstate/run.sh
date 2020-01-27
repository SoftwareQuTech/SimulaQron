simulaqron stop
simulaqron reset
simulaqron set backend stabilizer
simulaqron set max-qubits 1000
simulaqron set max-registers 1000
simulaqron start
python3 test_ghz_state.py "$@"
