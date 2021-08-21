#!/bin/bash

while read LINE
  do
    var=`echo $LINE | awk '{print $1}'` 
echo $var
    acnetget $var
done < $ACNET_VARIABLE_LIST_FILE
