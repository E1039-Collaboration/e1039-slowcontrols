# list of crates
set crate_list [list H1 H2 H3]

# array of PMT names
array set pmt_names {
0   H1XT
1   H1XB
2   H1YL
3   H1YR
4   H2XT
5   H2XB
6   H2YL
7   H2YR
8   H3XT
9   H3XB
10  H4XT-u
11  H4XT-d
12  H4XB-u
13  H4XB-d
14  H4Y1L-l
15  H4Y1L-r
16  H4Y1R-l
17  H4Y1R-r
18  H4Y2L-l
19  H4Y2L-r
20  H4Y2R-l
21  H4Y2R-r
22  LUMI
}

# array of numbers of each kind of PMT
array set pmt_numbers {
0   23
1   23
2   20
3   20
4   16
5   16
6   19
7   19
8   16
9   16
10  16
11  16
12  16
13  16
14  16
15  16
16  16
17  16
18  16
19  16
20  16
21  16
22  4
}

# array of maximum voltages of each kind of PMT
array set pmt_maxvolt {
0   -1800
1   -1800
2   -1800
3   -1800
4   -1800
5   -1800
6   -1800
7   -1800
8   -2100
9   -2100
10  -2100
11  -2100
12  -2100
13  -2100
14  -2100
15  -2100
16  -2100
17  -2100
18  -2100
19  -2100
20  -2100
21  -2100
22  -1000
}

set under "_"
set onoff_s "onoff"
set enabled_s "enabled"
set error_s "error"
set EN_s "EN"
set HV_s "HV"
set CM_s "CM"
set CE_s "CE"
set DV_s "DV"
set MV_s "MV"



grid columnconfigure . {1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23} -weight 1 -uniform a -minsize 30

# layout
# row 0 is for status of the three crates and the time
# row 1 is column headers, 1 through 23
# subsequent rows are for each PMT type
# column 0 has the PMT labels
# column 1 is PMT number 1, etc.

labelframe .crate_H1 -text "H1" -background white
label .crate_H1.enabled -textvariable H1_enabled -background white
label .crate_H1.onoff -textvariable H1_onoff -background white
label .crate_H1.error -textvariable H1_error -background white
grid .crate_H1 -row 0 -column 0 -columnspan 6
grid .crate_H1.enabled -row 0 -column 0 -columnspan 2
grid .crate_H1.onoff -row 0 -column 2 -columnspan 2
grid .crate_H1.error -row 0 -column 4 -columnspan 2

labelframe .crate_H2 -text "H2" -background white
label .crate_H2.enabled -textvariable H2_enabled -background white
label .crate_H2.onoff -textvariable H2_onoff -background white
label .crate_H2.error -textvariable H2_error -background white
grid .crate_H2 -row 0 -column 6 -columnspan 6
grid .crate_H2.enabled -row 0 -column 0 -columnspan 2
grid .crate_H2.onoff -row 0 -column 2 -columnspan 2
grid .crate_H2.error -row 0 -column 4 -columnspan 2

labelframe .crate_H3 -text "H3H4" -background white
label .crate_H3.enabled -textvariable H3_enabled -background white
label .crate_H3.onoff -textvariable H3_onoff -background white
label .crate_H3.error -textvariable H3_error -background white
grid .crate_H3 -row 0 -column 12 -columnspan 6
grid .crate_H3.enabled -row 0 -column 0 -columnspan 2
grid .crate_H3.onoff -row 0 -column 2 -columnspan 2
grid .crate_H3.error -row 0 -column 4 -columnspan 2

labelframe .display_time -text "Display Time" -background white
label .display_time.date -textvariable DATETIME -background white
grid .display_time -row 0 -column 18 -columnspan 6
grid .display_time.date -row 0 -column 0 -columnspan 6 

label .data_date_title -text "Data Time" -background white
grid .data_date_title -row 10 -column 18 -columnspan 6

label .data_date -textvariable DATA_TIME -background white
grid .data_date -row 11 -column 18 -columnspan 6 


proc open_expert_window {} {
    toplevel .ew
    label .ew.warning -text "FOR EXPERTS ONLY" -font bold -justify center -background red
    grid .ew.warning -row 0 -column 0 -columnspan 3
    label .ew.pmt_label -text "PMT TYPE"
    label .ew.chnl_label -text "CHNL"
    label .ew.voltage_label -text "VOLTAGE"
    grid .ew.pmt_label -row 1 -column 0
    grid .ew.chnl_label -row 1 -column 1
    grid .ew.voltage_label -row 1 -column 2
    entry .ew.pmt_type -width 10 -textvariable pmt_type
    entry .ew.chnl_number -width 10 -textvariable chnl_number
    entry .ew.voltage -width 10 -textvariable voltage
    grid .ew.pmt_type -row 2 -column 0
    grid .ew.chnl_number -row 2 -column 1
    grid .ew.voltage -row 2 -column 2
    button .ew.apply -command {apply_change $pmt_type $chnl_number $voltage} -text "APPLY" -font bold -justify center -background green
    grid .ew.apply -row 3 -column 1
    button .ew.close -command {destroy .ew} -text "CLOSE" -font bold -justify center -background cyan
    grid .ew.close -row 4 -column 1
    label .ew.blank -text "                  "
    grid .ew.blank -row 5 -column 0 -columnspan 3
    label .ew.hvonoff -text "HV CRATE ON/OFF" -font bold -justify center -background white
    grid .ew.hvonoff -row 6 -column 0 -columnspan 3
    label .ew.h1_label -text "H1 HV"
    label .ew.h2_label -text "H2 HV"
    label .ew.h3_label -text "H3H4 HV"
    grid .ew.h1_label -row 7 -column 0
    grid .ew.h2_label -row 7 -column 1
    grid .ew.h3_label -row 7 -column 2
    button .ew.h1_on -command {hv_on "H1"} -text "ON" -font bold -justify center -background red
    button .ew.h2_on -command {hv_on "H2"} -text "ON" -font bold -justify center -background red
    button .ew.h3_on -command {hv_on "H3"} -text "ON" -font bold -justify center -background red
    grid .ew.h1_on -row 8 -column 0
    grid .ew.h2_on -row 8 -column 1
    grid .ew.h3_on -row 8 -column 2
    button .ew.h1_off -command {hv_off "H1"} -text "OFF" -font bold -justify center -background green
    button .ew.h2_off -command {hv_off "H2"} -text "OFF" -font bold -justify center -background green
    button .ew.h3_off -command {hv_off "H3"} -text "OFF" -font bold -justify center -background green
    grid .ew.h1_off -row 9 -column 0
    grid .ew.h2_off -row 9 -column 1
    grid .ew.h3_off -row 9 -column 2
    label .ew.blank2 -text "                "
    grid .ew.blank2 -row 10 -column 0 -columnspan 3
    label .ew.hvcomms -text "HV CRATE COMMS"
    grid .ew.hvcomms -row 11 -column 0 -columnspan 3
    label .ew.h1comms_label -text "H1"
    label .ew.h2comms_label -text "H2"
    label .ew.h3comms_label -text "H3H4"
    grid .ew.h1comms_label -row 12 -column 0
    grid .ew.h2comms_label -row 12 -column 1
    grid .ew.h3comms_label -row 12 -column 2
    button .ew.h1comms_reset -command {hvcomms_reset "H1"} -text "RESET" -font bold -justify center -background green
    button .ew.h2comms_reset -command {hvcomms_reset "H2"} -text "RESET" -font bold -justify center -background green
    button .ew.h3comms_reset -command {hvcomms_reset "H3"} -text "RESET" -font bold -justify center -background green
    grid .ew.h1comms_reset -row 13 -column 0
    grid .ew.h2comms_reset -row 13 -column 1
    grid .ew.h3comms_reset -row 13 -column 2
    button .ew.h1_status -command {hv_status "H1"} -text "STATUS" -font bold -justify center -background green
    button .ew.h2_status -command {hv_status "H2"} -text "STATUS" -font bold -justify center -background green
    button .ew.h3_status -command {hv_status "H3"} -text "STATUS" -font bold -justify center -background green
    grid .ew.h1_status -row 14 -column 0
    grid .ew.h2_status -row 14 -column 1
    grid .ew.h3_status -row 14 -column 2
}

proc hvcomms_reset {cratename} {
    set message_string "Resetting $cratename comms\n"
    append message_string [exec ./reset_netrs232.sh -y $cratename]
    show_message [set message_string]
}

proc hv_status {cratename} {
    set message_string "Getting $cratename status\n"
    append message_string [exec ./status $cratename]
    show_message [set message_string]
}

proc hv_on {cratename} {
    show_message "Turning on $cratename HV"
    exec ./on $cratename
}

proc hv_off {cratename} {
    show_message "Turning off $cratename HV"
    exec ./off $cratename
}

proc apply_change {pmt chnl voltage} {
    set under "_"
    set found 0
    foreach i [array names ::pmt_names] {
	if {[string equal $::pmt_names($i) $pmt]} {
	    set found 1
	    break
	}
    }
    if {!$found} {
	show_message "$pmt is not a valid PMT type."
	return
    }
    if {$chnl < 1 || $chnl > $::pmt_numbers($i)} {
	show_message "$chnl is not a valid channel number for $pmt"
	return
    }
    if {$voltage > 0 || $voltage < $::pmt_maxvolt($i)} {
	show_message "$voltage is not a valid voltage for $pmt"
	return
    }
    foreach crate_chnl [array names ::map] {
	if {[string equal $::map($crate_chnl) $pmt$under$chnl]} {break}
    }
    set crate_chnl_strings [split $crate_chnl "_"]
    set crate_string [lindex $crate_chnl_strings 0]
    set chnl_string [lindex $crate_chnl_strings 1]
    show_message "Congratulations: $pmt $chnl $voltage is valid. \n The crate address is $crate_chnl \n The shell command will be set-channel $crate_string $chnl_string $voltage"
    exec ./set-channel $crate_string $chnl_string $voltage
}

proc show_message {message} {
    toplevel .sm 
    grid [label .sm.title -text "A message for you:"] -row 0
    label .sm.message -text $message
    grid .sm.message -row 1
    button .sm.close -command {destroy .sm} -text "CLOSE" -font bold -background cyan
    grid .sm.close -row 2
}

proc open_help_window {} {
    toplevel .help_window
    label .help_window.information -text "A red crate info box means you have lost communication with the crate: call an expert. \n A red high voltage value means the measured voltage differs from the demand voltage by more than 20 V; if this is new then call an expert. \n A red Data Time means the data is more than 5 minutes old: call an expert." -font bold
    grid .help_window.information -row 0
    button .help_window.close -command {destroy .help_window} -text "CLOSE" -font bold -background cyan
    grid .help_window.close -row 1
}

button .expert -command open_expert_window -text "EXPERT" -font bold -justify center -background green
grid .expert -column 20 -columnspan 2 -row 15 -rowspan 3

button .help -command open_help_window -text "HELP" -font bold -justify center -background green
grid .help -column 20 -columnspan 2 -row 18 -rowspan 3

button .exit -command exit -text "EXIT" -font bold -justify center -background cyan
grid .exit -column 20 -columnspan 2 -row 21 -rowspan 3

label .sigma_tag -text "Std. dev. from demand voltages:"
grid .sigma_tag -row 13  -column 17 -columnspan 5

label .sigma_value -textvariable sigma_demand
grid .sigma_value -row 13 -column 22

for {set i 1} {$i<24} {incr i} {
    label .header$i -text $i -font bold -justify center -background white
    grid .header$i -row 1 -column $i
}

for {set i 0} {$i<23} {incr i} {
    label .pmt$i -text $pmt_names($i) -background white
    grid .pmt$i -row [expr {$i + 2}] -column 0
    for {set j 1} {$j<$pmt_numbers($i)+1} {incr j} {
	label .pmt_$pmt_names($i)$under$j -textvariable $pmt_names($i)$under$j -background white
	grid .pmt_$pmt_names($i)$under$j -row [expr {$i + 2}] -column $j
    }
}



set state_enabled 0
set state_onoff 0
set state_maytrip 0

. configure -background white

# read the mapping files
# each lecroy channel has a name like H1_66
# each pmt has a name like H3XT_12
# then "set map(H1_66) H3XT_12" is how the map is constructed
foreach CRATEID $crate_list {
    set maplist [split [exec more ../settings/current/$CRATEID] "\n"]
    set limit [llength $maplist]
    for {set i 0} {$i<$limit} {incr i} {
	set chnlnumber [string range [lindex $maplist $i] 0 2]
	set chnlnumber [string trim $chnlnumber]
	set pmtname [string range [lindex $maplist $i] 8 14]
	set pmtname [string trim $pmtname]
	set pmtnumber [string range [lindex $maplist $i] 16 17]
	set pmtnumber [string trim $pmtnumber]
	if {![string equal $pmtname "Bad"]} {
	    set map($CRATEID$under$chnlnumber) $pmtname$under$pmtnumber
	}
    }
}



# this loop runs forever; press the EXIT button to stop

while {1} {

set devsum 0
set devcount 0

#get data from TSV file

set SLASH "/"
# find the latest slowcontrol directory
set DATA_DIR "/data2/e1039_data/slowcontrol_data"
set dirlist [split [exec ls $DATA_DIR -At | grep "slowcontrol"] "\n"]
# the first one in this list is the latest directory
set NEWEST_DIR [lindex $dirlist 0]
set filelist [split [exec ls $DATA_DIR$SLASH$NEWEST_DIR -At | grep "HodoHv"] "\n"]
# the first one in this list is the latest file
set NEWEST_FILE [lindex $filelist 0]


# split tsv file into separate lines
    set tsvdata [split [exec more $DATA_DIR$SLASH$NEWEST_DIR$SLASH$NEWEST_FILE] "\n"]
    set limit [llength $tsvdata]

    for {set i 0} {$i<$limit} {incr i} {
# each line has a name, a time, and a value, separated by tabs
	set linedata [split [lindex $tsvdata $i] "\t"]
	set dataname [string trim [lindex $linedata 0]]
	set datatime [string trim [lindex $linedata 1]]
	set datavalue [string trim [lindex $linedata 2]]

# each name has a type (a PMT type or "LC"), a location, and a descriptor, separated by underscores
	set name_parts [split $dataname "_"]
	set type [string trim [lindex $name_parts 0]]
	set location [string trim [lindex $name_parts 1]]
	set descriptor [string trim [lindex $name_parts 2]]

# if it is a LeCroy crate information variable...
	if {[string equal $type "LC"]} {
	    if {[string equal $descriptor "CM"]} {
		if {$datavalue == 1} {
		    .crate_$location configure -background white
		} else {.crate_$location configure -background red}
	    } elseif {[string equal $descriptor "EN"]} {
		if {$datavalue == 1} {
		    set $location$under$enabled_s "Enabled"
		} else {set $location$under$enabled_s "Disabled"}
	    } elseif {[string equal $descriptor "HV"]} {
		if {$datavalue == 1} {
		    set $location$under$onoff_s "ON"
		} else {set $location$under$onoff_s "OFF"}
	    } elseif {[string equal $descriptor "CE"]} {
		if {$datavalue == 1} {
		    set $location$under$error_s "has errors"
		} else {set $location$under$error_s "no errors"}
	    }
# otherwise it is a PMT information variable (first letter of $type is "H" or "L")
	} elseif {[string equal [string index $type 0] "H"] || [string equal [string index $type 0] "L"]} {
	    if {[string equal $descriptor "MV"]} {
		set $type$under$location $datavalue
		set mv_array($type$under$location) $datavalue
	    } elseif {[string equal $descriptor "DV"]} {
		set deviation [expr {abs($mv_array($type$under$location)-$datavalue)}]
		if {$deviation > 20} {
		    .pmt_$type$under$location configure -background red
		} else {
		    .pmt_$type$under$location configure -background white
		}
		set devsum [expr {$devsum + $deviation*$deviation}]
		incr devcount
	    }
	}
    }
	
if {$devcount > 0} {set sigma_demand [format "%.1f" [expr {sqrt($devsum/$devcount)}]]}

# check and display the current time and the data time

set DATETIME [exec date]
set DATETIME_UNIX [exec date +%s]

set command_string "@"
append command_string $datatime
set DATA_TIME [exec date -d [set command_string]]

if {[expr {$DATETIME_UNIX-$datatime}] > 300} {
    .data_date configure -background red
} else {.data_date configure -background white}



# this while waits 1 minute, but keeps Tcl awake so it can respond to user action
    set done 0
    after 60000 {set done 1}
    while {!$done} {update}
}
