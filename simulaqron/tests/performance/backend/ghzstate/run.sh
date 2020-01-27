simulaqron stop
simulaqron reset -f
simulaqron set backend stabilizer
simulaqron set max-qubits 1000
simulaqron set max-registers 1000
simulaqron start -f
python3 test_ghz_state.py "$@"
