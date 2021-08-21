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

labelframe .crate_H3 -text "H3" -background white
label .crate_H3.enabled -textvariable H3_enabled -background white
label .crate_H3.onoff -textvariable H3_onoff -background white
label .crate_H3.error -textvariable H3_error -background white
grid .crate_H3 -row 0 -column 12 -columnspan 6
grid .crate_H3.enabled -row 0 -column 0 -columnspan 2
grid .crate_H3.onoff -row 0 -column 2 -columnspan 2
grid .crate_H3.error -row 0 -column 4 -columnspan 2

label .date -textvariable DATETIME -background white
grid .date -row 0 -column 18 -columnspan 6 

button .exit -command exit -text "EXIT" -font bold -justify center -background blue
grid .exit -column 20 -columnspan 2 -row 21 -rowspan 3

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
    button .ew.close -command {destroy .ew} -text "CLOSE" -font bold -justify center -background blue
    grid .ew.close -row 4 -column 1
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
}

proc show_message {message} {
    toplevel .sm 
    grid [label .sm.title -text "A message for you:"] -row 0
    label .sm.message -text $message
    grid .sm.message -row 1
    button .sm.close -command {destroy .sm} -text "CLOSE" -font bold -background blue
    grid .sm.close -row 2
}

button .expert -command open_expert_window -text "EXPERT" -font bold -justify center -background green
grid .expert -column 20 -columnspan 2 -row 15 -rowspan 3

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

set min_lines 6
set start_line 6

# this loop runs forever; press the EXIT button to stop

while {1} {

    set DATETIME [exec "date"]

set devsum 0
set devcount 0

# loop over the crates
    foreach CRATEID $crate_list {

# get output of status command and process
# there are three kinds of status outputs
# 1 -- a single line and then no more information -- this is an error state
# 2 -- a single line and then an "Error" message -- this is an error state
# 3 -- many lines containing the enabled, status, and channel-error state
	set statuslist [split [exec ./status $CRATEID] "\n"]
	if {[llength $statuslist]<$min_lines} {
	    set has_error 1
	    set $CRATEID$under$enabled_s "No response from crate"
	    .crate_$CRATEID.enabled configure -background red
	    set $CRATEID$under$onoff_s ""
	    set $CRATEID$under$error_s ""
	} else {
	    set has_error 0
	    set $CRATEID$under$enabled_s [lindex $statuslist 5]
	    .crate_$CRATEID.enabled configure -background white
	    set $CRATEID$under$onoff_s [lindex $statuslist 6]
	    set $CRATEID$under$error_s [lindex $statuslist 7]
	}
	if {[string equal [set $CRATEID$under$enabled_s] "HV Enabled"]} {set state_enabled 1} else {set state_enabled 0}
	if {[string equal [set $CRATEID$under$onoff_s] "HV on"]} {set state_onoff 1} else {set state_onoff 0}
	set state_maytrip [expr {$state_enabled*$state_onoff}]
  
# if the crate is on speaking terms, then do the monitor command
	if {!$has_error} {
# get output of monitor command and process
	    set monitorlist [split [exec ./monitor $CRATEID] "\n"]
	    set has_error [string equal -length 5 [lindex $monitorlist 1] "Error"]
	    if {$has_error} {
		set $CRATEID$under$enabled_s [lindex $monitorlist 1]
		.crate_$CRATEID.enabled configure -background red
	    } else {
		for {set i 0} {$i<256} {incr i} {
		    
# check if this lecroy channel is connected to a PMT
		    if {[array names map -exact $CRATEID$under$i] != ""} {

# if yes, then get the actual value and put it in the textvariable for that PMT display label
			set sign_string [string index [lindex $monitorlist [expr {$start_line + $i}]] 27]
			set value [string range [lindex $monitorlist [expr {$start_line + $i}]] 28 31]
			if {[string equal $sign_string "-"]} {set sign -1} else {set sign +1}
			if {[string equal $value ""]} {set actual ""} else {set actual [expr {$sign*$value}]}
			set $map($CRATEID$under$i) $actual
# get the demand value
			set sign_string  [string index [lindex $monitorlist [expr {$start_line + $i}]] 9]
			set value [string range [lindex $monitorlist [expr {$start_line + $i}]] 10 13]
			if {[string equal $sign_string "-"]} {set sign -1} else {set sign +1}
			if {[string equal $value ""]} {set demand ""} else {set demand [expr {$sign*$value}]}
# check the deviation between the two; if more than 20 then set background red
			if {![string equal $actual ""] && ![string equal $demand ""]} { 
			    set deviation [expr {abs($actual-$demand)}]
			    if {$deviation > 20 && $state_maytrip} {
				.pmt_$map($CRATEID$under$i) configure -background red
			    } else {
				.pmt_$map($CRATEID$under$i) configure -background white
			    }
			    set devsum [expr {$devsum + $deviation*$deviation}]
			    incr devcount
			}
		    }
		}
	    }
	}
    }

    if {$devcount > 0} {set sigma_demand [format "%.1f" [expr {sqrt($devsum/$devcount)}]]}

# this loop waits 1 minute, but keeps Tcl awake so it can respond to user action
    set done 0
    after 60000 {set done 1}
    while {!$done} {update}
}
