#!/bin/bash

 for dir in */; do
 	cd $dir
 	sh doNew.sh
 	cd ..
 	sleep 1
 done
