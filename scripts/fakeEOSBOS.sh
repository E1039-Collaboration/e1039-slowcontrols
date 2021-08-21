#!/bin/bash

spillcounter_init=$(cat /data2/e1039/daq/slowcontrols/scripts/fake_spillid_storage.dat)
echo "spill id from file:" $spillcounter_init
caput SPILLCOUNTER $spillcounter_init

for (( ; ; )) do
    caput BOS 1
    sleep 2s
    caput BOS 0
    sleep 3s
    spillcounter=$(caget -t SPILLCOUNTER)
    spillcounter=$((spillcounter+1))
    caput SPILLCOUNTER $spillcounter
    caput EOS 1
    sleep 2s
    caput EOS 0
    sleep 53s
    echo $spillcounter > /data2/e1039/daq/slowcontrols/scripts/fake_spillid_storage.dat
done
