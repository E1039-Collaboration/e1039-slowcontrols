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


set state_enabled 0
set state_onoff 0
set state_CE 0

cd /data2/e1039/daq/slowcontrols/lecroy/hv

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


# loop over the crates
    foreach CRATEID $crate_list {

# get the time in unix format
# get output of status command and process
# there are three kinds of status outputs
# 1 -- a single line and then no more information -- this is an error state
# 2 -- a single line and then an "Error" message -- this is an error state
# 3 -- many lines containing the enabled, status, and channel-error state
	set DATETIME [exec date +%s]
	set statuslist [split [exec ./status $CRATEID] "\n"]
	if {[llength $statuslist]<$min_lines} {
	    set has_error 1
	    set $CRATEID$under$enabled_s "No response from crate"
	    set $CRATEID$under$onoff_s ""
	    set $CRATEID$under$error_s ""
	    puts "LC_$CRATEID$under$CM_s\t$DATETIME\t0\t0"
	} else {
	    set has_error 0
	    set $CRATEID$under$enabled_s [lindex $statuslist 5]
	    set $CRATEID$under$onoff_s [lindex $statuslist 6]
	    set $CRATEID$under$error_s [lindex $statuslist 7]
	    puts "LC_$CRATEID$under$CM_s\t$DATETIME\t1\t0"
	}
	if {[string equal [set $CRATEID$under$enabled_s] "HV Enabled"]} {set state_enabled 1} else {set state_enabled 0}
	if {[string equal [set $CRATEID$under$onoff_s] "HV on"]} {set state_onoff 1} else {set state_onoff 0}
	if {[string equal [set $CRATEID$under$error_s] "Ch error"]} {set state_CE 1} else {set state_CE 0}

  
# if the crate is on speaking terms, then do the monitor command
	if {!$has_error} {
	    puts "LC_$CRATEID$under$EN_s\t$DATETIME\t$state_enabled\t0"
	    puts "LC_$CRATEID$under$HV_s\t$DATETIME\t$state_onoff\t0"
	    puts "LC_$CRATEID$under$CE_s\t$DATETIME\t$state_CE\t0"
# get unix time
	    set DATETIME [exec date +%s]
# get output of monitor command and process
	    set monitorlist [split [exec ./monitor $CRATEID] "\n"]
	    set has_error [string equal -length 5 [lindex $monitorlist 1] "Error"]
	    if {$has_error} {
		set $CRATEID$under$enabled_s [lindex $monitorlist 1]
	    } else {
		for {set i 0} {$i<256} {incr i} {
		    
# check if this lecroy channel is connected to a PMT
		    if {[array names map -exact $CRATEID$under$i] != ""} {

# if yes, then get the actual value and put it in the textvariable for that PMT display label
			set sign_string [string index [lindex $monitorlist [expr {$start_line + $i}]] 27]
			set value [string range [lindex $monitorlist [expr {$start_line + $i}]] 28 31]
			if {[string equal $sign_string "-"]} {set sign -1} else {set sign +1}
			if {[string equal $value ""]} {set actual ""} else {set actual [expr {$sign*$value}]}
			puts "$map($CRATEID$under$i)$under$MV_s\t$DATETIME\t$actual\t0"
# get the demand value
			set sign_string  [string index [lindex $monitorlist [expr {$start_line + $i}]] 9]
			set value [string range [lindex $monitorlist [expr {$start_line + $i}]] 10 13]
			if {[string equal $sign_string "-"]} {set sign -1} else {set sign +1}
			if {[string equal $value ""]} {set demand ""} else {set demand [expr {$sign*$value}]}
			puts "$map($CRATEID$under$i)$under$DV_s\t$DATETIME\t$demand\t0"

		    }
		}
	    }
	}
    }




