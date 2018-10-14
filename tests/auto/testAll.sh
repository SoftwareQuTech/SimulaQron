#!/bin/bash

for dir in */; do
	cd $dir
	sh testAll.sh $@
	cd ..
	sleep 1
done

