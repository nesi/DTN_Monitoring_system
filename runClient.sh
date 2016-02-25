#!/bin/bash
#author : Se-young Yu
#Date : 02/26/2016

IP_addr='123.123.123.123' # IP address of the DTN connected to DTN network
IP_monitor='123.123.123.123' # IP address of the monitoring machine
IP_DTNS='123.123.123.123 123.123.123.124' # IP address of other DTNs seperated by space
data_location='/data/' # Location of the data storage folder
interface='en1' # name of the interface


echo "Starting Monitoring Clients"
mkdir log 2> /dev/null
python src/FlowMon.py  $IP_addr $data_location $IP_monitor $IP_DTNS >> ./log/FlowMon.log &
FlowMon_PID=$!
echo "Flowmon running PID = $FlowMon_PID"
python src/nmon_analyser.py $IP_addr $interface $IP_monitor >>  ./log/nmon.log &
nMon_PID=$!
echo "nmon_analyser running PID = $nMon_PID"
