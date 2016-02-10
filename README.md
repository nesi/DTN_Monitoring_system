#DTN_Monitoring_system
=======================

DTN monitoring system is a software to monitor performance of Data Transfer Nodes (DTNs).
It reads nmon output for TCP interface statistics and disk storage to generate network
and disk activities. It reports the data using python matplot library.

#Dependencies:
=======================

Nigel's performance Monitor (nmon) : http://nmon.sourceforge.net/pmwiki.php
Tested : AIX 6.1 and Linux (15e version)

Python 2.x : https://www.python.org/downloads/
Tested : Python 2.4 and 2.6

Python-numpy : 1.10.1 http://www.scipy.org/scipylib/download.html
Python-matplotlib: 1.5.0 http://matplotlib.org/1.5.1/index.html

#How to use:
=======================
To run the server, please configure runServer.sh file with the following information
IP_addr : IP address of the server that the monitoring machine is placed. It will be the IP address of the server and should be reachable from the clients
IP_DTNS : IP address of the all DTNs seperated by a space.
data_location : location of the transferred files to be stored.
interface : name of the interface used by the transfer.

Execute runServer.sh to run the server.

To run the client, please configure runClient.sh file with the following information
IP_addr : IP address of this DTN. This IP should be used to transfer file, and should not be the private IP inside NAT if used.
IP_monitor : IP address of the server.
IP_DTNS : IP address of the all DTNs seperated by a space.
data_location : location of the transferred files to be stored.
interface : name of the interface used by the transfer.

Execute runClient.sh to run the server.

To get the report, run python drawplot.py in server. It will ask you to choose the date you want to get report from. To get the report, navigate into ./result/date-wanted/ and look for .pdf file for TCP read/write and transfer speed data.