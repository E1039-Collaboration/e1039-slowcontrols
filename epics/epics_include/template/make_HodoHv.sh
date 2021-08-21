#!/bin/bash

#cp alarms_list_DPhodo_DP1_LT1.alhConfig alarms_list_DPhodo_DP(pl)_(quad)(brd).alhConfig
#
#template=records_list_HodoHv_status.template
temporary=test00.txt
filename=records_list_HodoHv_status.db
pl=(H1XT H1XB H1YL H1YR H2XT H2XB H2YL H2YR H3XT H3XB H4XT-u H4XT-d H4XB-u H4XB-d H4Y1L-l H4Y1L-r H4Y1R-l H4Y1R-r H4Y2L-l H4Y2L-r H4Y2R-l H4Y2R-r LUMI)
ch1=(23 23 20 20 16 16 19 19 16 16 16 16 16 16 16 16 16 16 16 16 16 16 4)
ch2=(12 12 10 10  8  8 10 10  8  8  8  8  8  8  8  8  8  8  8  8  8  8 4)
inp=(A B C D E F G H I J K L)

rm $temporary $filename
for index in "${!pl[@]}"; do 
    echo 'record(calc,"st_'${pl[$index]}'_MV_A"){'  >> $temporary
    echo '  field(DESC,"st_'${pl[$index]}'_MV_A group status")'  >> $temporary
    echo '  field(PINI,"1")'  >> $temporary
    for (( c=0; c<${ch2[$index]}; c++ ))
    do
	chn=$(( $c + 1 ))
	echo '  field(INP'${inp[$c]}',"'${pl[$index]}'_'$chn'_MV CPP MSS")' >> $temporary
    done
    echo '  field(CALC,"A")'  >> $temporary
    echo '}'  >> $temporary
    echo " "  >> $temporary

    echo 'record(calc,"st_'${pl[$index]}'_MV_B"){'  >> $temporary
    echo '  field(DESC,"st_'${pl[$index]}'_MV_B group status")'  >> $temporary
    echo '  field(PINI,"1")'  >> $temporary
    for (( c=${ch2[$index]}; c<${ch1[$index]}; c++ ))
    do
	c2=$(( $c - ${ch2[$index]} ))
	chn=$(( $c + 1 ))
	echo '  field(INP'${inp[$c2]}',"'${pl[$index]}'_'$chn'_MV CPP MSS")' >> $temporary
    done
    echo '  field(CALC,"A")'  >> $temporary
    echo '}'  >> $temporary
    echo " "  >> $temporary

done

cp  $temporary $filename


