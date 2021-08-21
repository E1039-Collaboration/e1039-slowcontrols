
Hall Environmental Monitoring
=============================

This directory contains software to read out the Keithley 2701 digital multimeter.

## Important notes
* Run only one instance of this program at a time.
* The kscan program reads the hall environmental sensors once each and then exits.  There are no inputs needed, and kscan outputs the measurements in TSV format to stdout.
* The program should take about 3 seconds to complete.

The measurement units are:
* Temperatures: degrees C
* Relative Humidity: %
* Dewpoints: degrees C
* Pressure: psi


