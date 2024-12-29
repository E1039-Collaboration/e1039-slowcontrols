#!/bin/sh

source /data2/e1039/this-e1039.sh
source /data2/e1039/daq/slowcontrols/scripts/setup_slowcontrols.sh

ALH_CFG_DIR=$SLOWCONTROL_ROOT/epics/epics_alh
ALH_LOG_DIR=/data2/e1039_data/slowcontrol_logs/alh_logs

echo "$ALH_DIR"

alh \
    -f $ALH_CFG_DIR\
    -l $ALH_LOG_DIR\
    -a e1039_alh_alarms.log\
    -o e1039_alh_operation.log\
    -global\
    -m 5000\
    -L\
    -Lfile ./e1039_lock.LOCK\
     alarms_list_SpinQuest.alhConfig

#e1039_alh_lock
