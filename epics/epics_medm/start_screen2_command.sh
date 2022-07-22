#!/bin/bash

source /data2/e1039/this-e1039.sh
source /data2/e1039/daq/slowcontrols/scripts/setup_slowcontrols.sh

MEDM_DIR=$SLOWCONTROL_ROOT/epics/epics_medm

X0=1920 # 260

medm \
     -x\
     -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"\
     -attach\
     -dg +$(( X0 ))+0\
      $MEDM_DIR/medm_Acnet.adl &

sleep 1s

medm \
     -x\
     -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"\
     -attach\
     -dg +$(( X0 ))+287\
      $MEDM_DIR/medm_SpillData.adl &

sleep 1s

medm \
     -x\
     -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"\
     -attach\
     -dg +$(( X0 + 410 ))+287\
      $MEDM_DIR/medm_BeamDAQ.adl &

sleep 1s

medm \
     -x\
     -displayFont "-bitstream-courier 10 pitch-medium-r-normal--0-0-0-0-m-0-iso8859-1"\
     -attach\
     -dg +$(( X0 + 910 ))+287\
      $MEDM_DIR/medm_ScalerDAQ.adl &
    

#medm -attach -dg +310+63 medm_Acnet.adl &
#sleep 1s
#medm -attach -dg +310+350 medm_SpillData.adl &
#medm -attach -dg +1110+350 medm_BeamDAQ.adl &
#medm -attach -dg +1180+687 medm_HallEnv.adl &


#medm -attach -dg +260+0 medm_Acnet.adl &
#sleep 1s
#medm -attach -dg +260+287 medm_SpillData.adl &
#medm -attach -dg +670+287 medm_BeamDAQ.adl &
#medm -attach -dg +1170+287 medm_ScalerDAQ.adl &
    

