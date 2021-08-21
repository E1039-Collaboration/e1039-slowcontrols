#!/bin/bash
# This script resets the 4 Port RS232 Serial over IP Ethernet Device Server,
# StarTech NETRS232_4 (https://www.startech.com/support/NETRS232_4).
# Usage: 
#   ./reset_netrs232.sh H1    ... Reset the H1 interface with confirmation.
#   ./reset_netrs232.sh -y H1 ... Reset the H1 interface without confirmation.
# Advanced usage:
#   ./reset_netrs232.sh -t 10 H1     ... Reset the H1 interface with a telnet time out of 10 s.
#   ./reset_netrs232.sh -t 5 -n 3 H1 ... Reset the H1 interface with a telnet time out of 5 s and three trials.

DIR_LECROY=$(readlink -f $(dirname $0)/../)

DO_ASK='yes'
TIME_OUT=60 # Telnet time out in second
N_TRY=1 # N of telnet trials
while getopts ":yt:n:" OPT ; do
    case $OPT in
	y ) DO_ASK='no' ;;
	t ) TIME_OUT=$OPTARG ;;
	n ) N_TRY=$OPTARG ;;
    esac
done
shift $((OPTIND - 1))

STA=$1 # H1, H2, H3 or H4
ADDR=$(grep "^$STA " $DIR_LECROY/settings/HVcrates | cut -d' ' -f3)
echo "Station = $STA, Address =  $ADDR"
if [ -z "$ADDR" ] ; then
    echo "The station name given is not supported.  Abort."
    exit 1
fi

if [ $DO_ASK = 'yes' ] ; then
    echo -n "Enter 'yes' to move into action: "
    read YESNO
    if [ "X$YESNO" != 'Xyes' ] ; then
	echo "  Abort."
	exit 0
    fi
fi

RET=1
for (( I_TRY = 1 ; I_TRY <= N_TRY ; I_TRY++)) ; do
    test $N_TRY -ne 1 && echo "Try #$I_TRY."
    timeout $TIME_OUT expect <<-EOF
	spawn telnet $ADDR
	expect "CMD:"
	send "login\n"
	expect "Please enter your password:"
	send "admin\n"
	expect "ACMD:"
	send "reset\n"
	expect "Do you wish to reboot device ?(Press Y/N+<Enter> to confirm)"
	send "Y\n"
	expect "System is reset. Please close this Telnet session."
	close
	EOF
    RET=$?
    test $RET -eq 0 && break
done

test $RET -ne 0 && echo "Failed (ret = $RET)."
exit $RET

#send "status\n"
#expect "ACMD:"
