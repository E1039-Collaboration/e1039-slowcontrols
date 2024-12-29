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
setenv EPICS_BASE /data2/epics-7.06.1/base-7.0.6
setenv EPICS_HOST_ARCH linux-x86_64
set arch = `uname -m`
if( $arch == "i686" ) then
  setenv EPICS_HOST_ARCH linux-x86
endif

setenv LD_LIBRARY_PATH ${EPICS_BASE}/lib/${EPICS_HOST_ARCH}/:${LD_LIBRARY_PATH}
setenv PATH ${EPICS_BASE}/bin/${EPICS_HOST_ARCH}:${PATH}

alias medm 'medm -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"'


#EPICS archiver
set thisHost=`hostname -s`
if ( $thisHost == "e1039gat1" ) then
  setenv ARCHAPPL_SHORT_TERM_FOLDER /home/epics/archiver/archappl_short_term
  setenv ARCHAPPL_MEDIUM_TERM_FOLDER /home/epics/archiver/archappl_medium_term
  setenv ARCHAPPL_LONG_TERM_FOLDER /home/epics/archiver/archappl_long_term
endif
#end of EPICS setup
