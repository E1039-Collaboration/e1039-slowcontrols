#!/bin/bash

source /data2/e1039/this-e1039.sh
source /data2/e1039/daq/slowcontrols/scripts/setup_slowcontrols.sh

MEDM_DIR=$SLOWCONTROL_ROOT/epics/epics_medm

medm \
     -x\
     -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"\
     -attach\
     -dg +260+0\
      $MEDM_DIR/medm_ChamHv.adl &

sleep 1s

medm \
     -x\
     -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"\
     -attach\
     -dg +260+287\
      $MEDM_DIR/medm_HodoHv.adl &

sleep 1s

medm \
     -x\
     -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"\
     -attach\
     -dg +260+624\
      $MEDM_DIR/medm_DPhodo.adl &

sleep 1s

medm \
     -x\
     -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"\
     -attach\
     -dg +1130+624\
      $MEDM_DIR/medm_HallEnv.adl &
    


#medm -attach -dg +310+63 medm_ChamHv.adl &
#sleep 1s
#medm -attach -dg +310+350 medm_HodoHv.adl &
#medm -attach -dg +310+687 medm_DPhodo.adl &
#medm -attach -dg +1180+687 medm_HallEnv.adl &
    
