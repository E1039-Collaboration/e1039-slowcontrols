#!/bin/bash

file=$1

while read st channel voltage
do
  /data2/e1039/daq/slowcontrols/lecroy/hv/set-channel $st $channel $voltage
  sleep 2
done < $file
