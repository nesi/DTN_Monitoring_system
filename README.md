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

#Running each component:
=======================
Each component can be run separately with following instruction

DTNMON: Do not require any parameter. 

FlowMon : Require 4+ arguments in order, separated by space.
1st arg = IP address of the DTN it is running
2nd arg = Physical location of data
3rd arg = IP address of DTNMon to report
4th+ arg = IP address(es) of other DTN to watch

nmon_analyser : Require 3 argments in order, sepearted by space.
1st arg = IP address of the DTN it is running
2nd arg = Interface name to watch
3rd arg = IP address of DTNMon to report

#Components:
=======================
DTNMon : A server that receives data sent from clients and archive them in the local result directory. It listens to TCP port 50000, receives serialised python objects (Flow_data and System_data) and deserialize them. It builds flow table for transfers (both one-way and two-way) and watches transfer speed. It generates output from Flow data and System data received in CSV format. Currently, it only watches the transfer speed from flow_table, but it can be extended to alarm the user when the speed drops below certain point.

FlowMon : A client that watches TCP port >50000 and < 51000 to watch transfers. It uses netstat each seconds to check whether there is any transfer is happening. It creates Flow instances from actual transfer using 5 tuple information, append number of bytes transferred using TransferMon, archive them for a minute and sends the archive to the server.

TransferMon : A scripts that checks files size of a specific directory(this case, it is a transfer location). It stores all the file sizes in the folder and check the differences each second to calculate how many bytes added to the directory.

nmon_analyser: A client that runs nmon for each second and analyse its output. Currently, it watches TCP socket read/write and physical CPU times for user and system. It creates System data instances from the nmon output, archives for a second and sends to the server.