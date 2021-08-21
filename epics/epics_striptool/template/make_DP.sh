#!/bin/bash

#template=striptool_DPhodo_DP1_LT1_I.stp.tmpl
#template=striptool_DPhodo_DP1_LT1_T.stp.tmpl
#template=striptool_DPhodo_DP1_LT1_V.stp.tmpl
#template=striptool_DPhodo_DP1_LT1_chI_01_08.stp.tmpl
#template=striptool_DPhodo_DP1_LT1_chI_09_16.stp.tmpl
#template=striptool_DPhodo_DP1_LT1_chI_17_24.stp.tmpl
#template=striptool_DPhodo_DP1_LT1_chV_01_08.stp.tmpl
#template=striptool_DPhodo_DP1_LT1_chV_09_16.stp.tmpl
template=striptool_DPhodo_DP1_LT1_chV_17_24.stp.tmpl

this_template=${template%.*}
echo $template
pl="1 2"
quad="LT RT LB RB"
brd1="1 2 3 4"
brd2="1 2"

for v_pl in $pl; do
 if [[ "$v_pl" == "1" ]]; then 
     brd=$brd1 
 fi
 if [[ "$v_pl" == "2" ]]; then 
     brd=$brd2
 fi
 for v_quad in $quad; do
  for v_brd in $brd; do
      echo $v_pl$v_quad$v_brd
      file_name=${this_template//DP1/DP$v_pl}
      file_name=${file_name//LT1/$v_quad$v_brd}
      echo $template $file_name
      cp $template  $file_name
      sed -i 's/DP1/DP'$v_pl'/g' $file_name
      sed -i 's/LT1/'$v_quad$v_brd'/g' $file_name
      sed -i 's/LT qdrnt/'$v_quad' qdrnt/g' $file_name
      sed -i 's/brd 1/brd '$v_brd'/g' $file_name
  done
 done
done
