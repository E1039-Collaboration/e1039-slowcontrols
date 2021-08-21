#!/bin/bash

#cp alarms_list_DPhodo_DP1_LT1.alhConfig alarms_list_DPhodo_DP(pl)_(quad)(brd).alhConfig
#
#template=records_list_HodoHv_status.template
temporary=test00.txt
filename=records_list_DPhodo_status.db
pl="1 2"
quad="LT RT LB RB"
brd1="1 2 3 4"
brd2="1 2"
vi="V I" 
inp=(A B C D E F G H I J K L)

rm $temporary $filename
for v_pl in $pl; do
 if [[ "$v_pl" == "1" ]]; then
     brd=$brd1
 fi
 if [[ "$v_pl" == "2" ]]; then
     brd=$brd2
 fi
 for v_quad in $quad; do
  for v_brd in $brd; do

    echo 'record(calc,"st_DP'$v_pl'_'$v_quad$v_brd'"){'  >> $temporary
    echo '  field(DESC,"st_DP'$v_pl'_'$v_quad$v_brd' group status")'  >> $temporary
    echo '  field(PINI,"1")'  >> $temporary
    echo '  field(INPA,"st_DP'$v_pl'_'$v_quad$v_brd'_TVI CPP MSS")'  >> $temporary
    echo '  field(INPB,"st_DP'$v_pl'_'$v_quad$v_brd'_CHV_A CPP MSS")'  >> $temporary
    echo '  field(INPC,"st_DP'$v_pl'_'$v_quad$v_brd'_CHV_B CPP MSS")'  >> $temporary
    echo '  field(INPD,"st_DP'$v_pl'_'$v_quad$v_brd'_CHI_A CPP MSS")'  >> $temporary
    echo '  field(INPE,"st_DP'$v_pl'_'$v_quad$v_brd'_CHI_B CPP MSS")'  >> $temporary
    echo '  field(CALC,"A")'  >> $temporary
    echo '}'  >> $temporary
    echo " "  >> $temporary

    #---------------------------------------------------------------------------

    echo 'record(calc,"st_DP'$v_pl'_'$v_quad$v_brd'_TVI"){'  >> $temporary
    echo '  field(DESC,"st_DP'$v_pl'_'$v_quad$v_brd'_TVI group status")'  >> $temporary
    echo '  field(PINI,"1")'  >> $temporary
    echo '  field(INPA,"DP'$v_pl'_'$v_quad$v_brd'_TPLATE CPP MSS")'  >> $temporary
    echo '  field(INPB,"DP'$v_pl'_'$v_quad$v_brd'_TPREAMP CPP MSS")'  >> $temporary
    echo '  field(INPC,"DP'$v_pl'_'$v_quad$v_brd'_V9 CPP MSS")'  >> $temporary
    echo '  field(INPD,"DP'$v_pl'_'$v_quad$v_brd'_VDD CPP MSS")'  >> $temporary
    echo '  field(INPE,"DP'$v_pl'_'$v_quad$v_brd'_V100 CPP MSS")'  >> $temporary
    echo '  field(INPF,"DP'$v_pl'_'$v_quad$v_brd'_VPREAMP CPP MSS")'  >> $temporary
    echo '  field(INPG,"DP'$v_pl'_'$v_quad$v_brd'_IPREAMP CPP MSS")'  >> $temporary
    echo '  field(CALC,"A")'  >> $temporary
    echo '}'  >> $temporary
    echo " "  >> $temporary

    #---------------------------------------------------------------------------

    for v_vi in $vi; do
     echo 'record(calc,"st_DP'$v_pl'_'$v_quad$v_brd'_CH'$v_vi'_A"){'  >> $temporary
     echo '  field(DESC,"st_DP'$v_pl'_'$v_quad$v_brd'_CH'$v_vi'_A group status")'>>$temporary
     echo '  field(PINI,"1")'  >> $temporary
     for (( c=0; c<12; c++ )) do
      chn=$(( $c + 1 ))
      echo '  field(INP'${inp[$c]}',"DP'$v_pl'_'$v_quad$v_brd'_CH'$chn'_'$v_vi' CPP MSS")'>>$temporary
     done
     echo '  field(CALC,"A")'  >> $temporary
     echo '}'  >> $temporary
     echo " "  >> $temporary

     #---------------------------------------------------------------------------

     echo 'record(calc,"st_DP'$v_pl'_'$v_quad$v_brd'_CH'$v_vi'_B"){'  >> $temporary
     echo '  field(DESC,"st_DP'$v_pl'_'$v_quad$v_brd'_CH'$v_vi'_B group status")'>>$temporary
     echo '  field(PINI,"1")'  >> $temporary
     for (( c=12; c<24; c++ )) do
      c2=$(( $c - 12 ))
      chn=$(( $c + 1 ))
      echo '  field(INP'${inp[$c2]}',"DP'$v_pl'_'$v_quad$v_brd'_CH'$chn'_'$v_vi' CPP MSS")'>>$temporary
     done
     echo '  field(CALC,"A")'  >> $temporary
     echo '}'  >> $temporary
     echo " "  >> $temporary

    done

  done
 done
done

cp  $temporary $filename


