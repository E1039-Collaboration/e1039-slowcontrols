#!/bin/tcsh

# 7 July 2019 PEReimer
# Old version of this script tried to do some fance shell scripting to figure out the correct 
# #location (see /data2/e906daq/seaquest-daq/SlowControls/...) I've just hardcoded the 
# environmental variables here.
#

setenv SLOWCONTROL_ROOT /data2/e1039/daq/slowcontrols
#echo $SLOWCONTROL_ROOT
setenv PYTHONPATH "$SLOWCONTROL_ROOT/pylib"

#setup ACNET
setenv PATH "$SLOWCONTROL_ROOT/acnet":"$PATH"
#end ACNET

#setup EPICS
setenv EPICS_CA_ADDR_LIST e1039gat1.sq.pri
setenv EPICS_BASE /data2/epics-7.0.2.2/base-7.0.2.2
setenv EPICS_HOST_ARCH linux-x86_64
set arch = `uname -m`
if( $arch == "i686" ) then
  setenv EPICS_HOST_ARCH linux-x86
endif

#echo "EPICS_HOST_ARCH = " $EPICS_HOST_ARCH

setenv PATH ${EPICS_BASE}/bin/${EPICS_HOST_ARCH}:${PATH}

alias medm 'medm -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"'
#end of EPICS setup
