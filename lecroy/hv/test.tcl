set SLASH "/"
# find the latest HV data
set DATA_DIR "/data2/e1039_data/slowcontrol_data"
set dirlist [split [exec ls $DATA_DIR -At | grep "slowcontrol"] "\n"]
# the first one in this list is the latest directory
set NEWEST_DIR [lindex $dirlist 0]
set filelist [split [exec ls $DATA_DIR$SLASH$NEWEST_DIR -At | grep "HodoHv"] "\n"]
# the first one in this list is the latest file
set NEWEST_FILE [lindex $filelist 0]







