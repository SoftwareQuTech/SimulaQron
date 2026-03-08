#!/usr/bin/env bash

START_SIMULAQRON=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--no-start-simulaqron)
            START_SIMULAQRON=false
            shift
            ;;
    esac
done

if [ "$START_SIMULAQRON" = true ]; then
    if [ ! -f ~/.simulaqron_pids/simulaqron_network_default.pid ]; then
        simulaqron start --nodes=Alice --network-config-file simulaqron_network.json --simulaqron-config-file simulaqron_settings.json
    fi
fi

python3 nodeTest.py
