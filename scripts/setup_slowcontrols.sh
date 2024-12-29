#!/usr/bash

#setup Slowcontrol
export SLOWCONTROL_ROOT=/data2/e1039/daq/slowcontrols
export PYTHONPATH=$SLOWCONTROL_ROOT/pylib
#end Slowcontrol

#setup ACNET
export PATH=$SLOWCONTROL_ROOT/acnet:$PATH
#end ACNET

#setup EPICS
#2021 Nov 15 PEReimer changed server to e1039scrun.sc.pri and base to epics-7.0.6
export EPICS_BASE=/data2/epics-7.06.1/base-7.0.6
export EPICS_CA_ADDR_LIST=e1039scrun.sq.pri

export EPICS_HOST_ARCH=linux-x86_64
arch=`uname -m`
if [ "$arch" == "i686" ]; then
  export EPICS_HOST_ARCH=linux-x86
fi
export LD_LIBRARY_PATH=${EPICS_BASE}/lib/${EPICS_HOST_ARCH}/:${LD_LIBRARY_PATH}
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
