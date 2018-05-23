#!/bin/bash
ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep setup | awk {'print $2'} | xargs kill -9
ps aux | grep python | grep start | awk {'print $2'} | xargs kill -9
echo "Starting tests"
cd "$NETSIM"/tests/auto
sh testAll.sh

