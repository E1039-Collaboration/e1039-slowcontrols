#!/bin/sh

source /data2/e1039/daq/slowcontrols/scripts/setup_slowcontrols.sh
#E906 root setup files
#source /data2/software/current/setup.sh
#E1039 root setup file
source /data2/e1039/this-e1039.sh
$SLOWCONTROL_ROOT/epics/epics_scripts/fill_epics_var_1

