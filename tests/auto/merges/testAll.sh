#!/bin/bash

# NOTE THAT WE ASSUME THAT SERVERS ARE ALREADY RUNNING

 for dir in */; do
 	cd $dir
 	sh doNew.sh
 	cd ..
 	sleep 1
 done
