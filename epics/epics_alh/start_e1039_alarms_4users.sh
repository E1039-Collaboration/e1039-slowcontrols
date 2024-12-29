#!/bin/sh

source /data2/e1039/this-e1039.sh
source /data2/e1039/daq/slowcontrols/scripts/setup_slowcontrols.sh

ALH_CFG_DIR=$SLOWCONTROL_ROOT/epics/epics_alh
ALH_LOG_DIR=/data2/e1039_data/slowcontrol_logs/alh_logs

echo "$ALH_DIR"

alh \
    -f $ALH_CFG_DIR\
    -l $ALH_LOG_DIR\
    -D\
    -S\
    alarms_list_SpinQuest.alhConfig

    

