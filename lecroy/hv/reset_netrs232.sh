#!/bin/bash
#!/usr/bin/tclsh
# This script resets the 4 Port RS232 Serial over IP Ethernet Device Server,
# StarTech NETRS232_4 (https://www.startech.com/support/NETRS232_4).
# Usage: 
#   ./reset_netrs232.sh H1    ... Reset the H1 interface with confirmation.
#   ./reset_netrs232.sh -y H1 ... Reset the H1 interface without confirmation.

DIR_LECROY=$(readlink -f $(dirname $0)/../)

DO_ASK='yes'
while getopts "y" OPT ; do
    case $OPT in
	y ) DO_ASK='no' ;;
    esac
done
shift $((OPTIND - 1))

STA=$1 # H1, H2, H3 or H4
ADDR=$(grep "^$STA " $DIR_LECROY/settings/HVcrates | cut -d' ' -f3)
echo "Station = $STA, Address =  $ADDR"
#echo "Station = $STA, Address = $ADDR"
if [ -z "$ADDR" ] ; then
    echo "The station name given is not supported.  Abort."
    exit
fi

if [ $DO_ASK = 'yes' ] ; then
    echo -n "Enter 'yes' to move into action: "
    read YESNO
    if [ "X$YESNO" != 'Xyes' ] ; then
	echo "  Abort."
	exit
    fi
fi

expect <<EOF
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

#send "status\n"
#expect "ACMD:"
