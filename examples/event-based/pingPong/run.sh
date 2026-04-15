#!/usr/bin/env bash
#
# Runs the ping-pong example.
#
# This example is purely classical — no quantum operations — so the
# SimulaQron backend (QNodeOS / virtual nodes) does not need to be started.
#
# On two separate machines, run these commands in separate terminals:
#   Machine B (Bob):   python3 pingpongBob.py
#   Machine A (Alice): python3 pingpongAlice.py
#
# On a single machine (this script):
#   Bob starts in the background, Alice in the foreground.

# cd to the example directory so relative paths in the scripts work correctly
cd "$(dirname "$0")"

# -u disables Python's output buffering so Bob's prints appear immediately
# even when running in the background on the same machine.
python3 -u pingpongBob.py &
BOB_PID=$!

sleep 1

python3 pingpongAlice.py

# Alice is done — shut Bob down
kill $BOB_PID 2>/dev/null
wait $BOB_PID 2>/dev/null
