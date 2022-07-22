#!/bin/bash

source /data2/e1039/this-e1039.sh
source /data2/e1039/daq/slowcontrols/scripts/setup_slowcontrols.sh

MEDM_DIR=$SLOWCONTROL_ROOT/epics/epics_medm
cd $MEDM_DIR

#medm $1 -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1" -attach -dg +50+100 spinQuest.adl 

medm \
     -x\
     -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"\
     -attach\
     -dg +0+0\
      $MEDM_DIR/medm_SpinQuest.adl 


