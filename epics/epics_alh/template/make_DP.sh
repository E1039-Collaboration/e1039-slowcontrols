#!/bin/bash

#cp alarms_list_DPhodo_DP1_LT1.alhConfig alarms_list_DPhodo_DP(pl)_(quad)(brd).alhConfig
#

pl="1 2"
quad="LT RT LB RB"
brd1="1 2 3 4"
brd2="1 2"

for v_pl in $pl; do
 if [[ "$v_pl" == "1" ]]; then 
     brd=$brd1
     template=alarms_list_DPhodo_DP1_LT.template
 fi
 if [[ "$v_pl" == "2" ]]; then 
     brd=$brd2
     template=alarms_list_DPhodo_DP2_LT.template
 fi
 for v_quad in $quad; do
  for v_brd in $brd; do
      echo $v_pl$v_quad$v_brd
      file_name='alarms_list_DPhodo_DP'$v_pl'_'$v_quad$v_brd'.alhConfig'
      #echo $template $file_name
      cp $template  $file_name
      sed -i 's/GROUP NULL 1/GROUP NULL '$v_brd'/g' $file_name
      sed -i 's/GROUP 1/GROUP '$v_brd'/g' $file_name
      sed -i 's/DP1/DP'$v_pl'/g' $file_name
      sed -i 's/LT1/'$v_quad$v_brd'/g' $file_name
  done
 done
done
