#!/bin/bash
#author : Se-young Yu
#Date : 02/26/2016

IP_addr='123.123.123.124' # IP address of the DTN monitor
IP_DTNS='123.123.123.123 123.123.123.124' # IP address of other DTNs seperated by space
data_location='/projects/uoa1234' # Location of the data storage folder
interface='eth2'

port_available=`netstat -t|grep 50000`


if [ -z "$port_available" ];
	then
		echo "Starting Monitoring Clients"
		mkdir log 2> /dev/null
		python -u src/DTNMon.py >> ./log/DTNMonitor.log &
		DTNMON_PID=$!
		echo "DTNMON running PID = $DTNMON_PID"
		python -u src/FlowMon.py $IP_addr $data_location $IP_addr $IP_DTNS >> ./log/FlowMon.log &
		FlowMon_PID=$!
		echo "Flowmon running PID = $FlowMon_PID"
		python -u src/nmon_analyser.py $IP_addr $interface $IP_addr >>  ./log/nmon.log &
		nMon_PID=$!
		echo "nmon_analyser running PID = $nMon_PID"
	
	else
		echo "port 50000 is not available. It is used by :"
		echo $port_available
fi
