#!/usr/bash

#setup Slowcontrol
export SLOWCONTROL_ROOT=/data2/e1039/daq/slowcontrols
export PYTHONPATH=$SLOWCONTROL_ROOT/pylib
#end Slowcontrol

#setup ACNET
export PATH=$SLOWCONTROL_ROOT/acnet:$PATH
#end ACNET

#setup EPICS
export EPICS_CA_ADDR_LIST=e1039gat1.sq.pri
#export EPICS_CA_ADDR_LIST=192.168.24.71
#export EPICS_CA_ADDR_LIST=e1039gat1.fnal.gov
#export EPICS_CA_ADDR_LIST=e906-gat6.fnal.gov
export EPICS_BASE=/data2/epics-7.0.2.2/base-7.0.2.2
export EPICS_HOST_ARCH=linux-x86_64
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$EPICS_BASE/lib/$EPICS_HOST_ARCH/
arch=`uname -m`
if [ "$arch" == "i686" ]; then
  export EPICS_HOST_ARCH=linux-x86
fi
export PATH=${EPICS_BASE}/bin/${EPICS_HOST_ARCH}:${PATH}
alias medm='medm -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"'

#EPICS archiver
thisHost=`hostname -s`
if [ "$thisHost" == "e1039gat1" ]; then
  export ARCHAPPL_SHORT_TERM_FOLDER=/home/epics/archiver/archappl_short_term
  export ARCHAPPL_MEDIUM_TERM_FOLDER=/home/epics/archiver/archappl_medium_term
  export ARCHAPPL_LONG_TERM_FOLDER=/home/epics/archiver/archappl_long_term
fi
#end EPICS
