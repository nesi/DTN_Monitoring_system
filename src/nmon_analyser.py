#!/usr/bin/python
#author : Se-young Yu
#Date : 02/26/2016
#comment: This module runs nmon for predifined period and analyse the output.
#The output analysed is sent to the DTN monitor

import time, sys, csv, os, threading, platform, signal
import shlex, subprocess

import socket, pickle

nmon_dir = '.'
nmon_period = 60 # Do not set less than 60!


#This class represents system data measured from nmon each second
class System_Data:

	def __init__(self,hostname):
	    self.hostname = hostname
	    self.unixtime = 0
	    self.cpu_usertime = 0
	    self.cpu_system = 0
	    self.network_read = 0
	    self.network_write = 0

	def __str__(self):
	    return ('hostname = {5}, time ={0}, cpu_user = {1},'
                    'cpu_system = {2}, network_read = {3}, network_write = {4}'
                    ''.format(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.unixtime)),
                    self.cpu_usertime, self.cpu_systime, self.network_read,
                    self.network_write, self.hostname))

#This class runs nmon for a period and analyse the output
class Nmon_analyser(threading.Thread):

    def __init__(self,myIP,interface, DTN_monitor):
        threading.Thread.__init__(self)
        self.DTN_Monitor = DTN_monitor
        self.interface = interface
        self.IP = myIP
        #print('initialised')

    def run(self):
        #print('thread running')
        for file in os.listdir(nmon_dir):
            if file.endswith(".nmon"):
                print('[{1}]\tanalysing {0}'.format(file,time.time()))
                data_list = self.analyse(self.interface, file)
                if len(data_list) == nmon_period:
                    data_list.insert(0,self.IP)
                    print('[{1}]\tsending {0}'.format(file,time.time()))
                    self.send_data(self.DTN_Monitor, data_list)
                    os.remove(file) # remove analysed file
                    print('[{1}]\tremove {0}'.format(file,time.time()))
                    

    #sending analysed output to the DTN monitor
    def send_data(self,DTN_Monitor,data_list):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((DTN_Monitor, 50000))
        s.sendall(pickle.dumps(data_list, -1))        
        s.close()

    #analyse the output file
    def analyse(self,interface, filename):
        data_list = []
        index = 0
        current_data = None

        if platform.system() == 'AIX':
            cpu_header = 'PCPU_ALL'
        elif platform.system() == 'Linux':
            cpu_header = 'CPU_ALL'

        with open(filename, 'rb') as csvfile: # read nmon outout and generate system record object
            nmonreader = csv.reader(csvfile, delimiter=',')
            for row in nmonreader:
                
                if row[0] == 'AAA' and row[1] == 'host':
                    print('[{0}]\tcreating data'.format(time.time()))
                    hostname = row[2]                    

                elif row[0] == 'NET' and 'Network I/O' in row[1] :
                    nic_read_column = row.index(interface+'-read-KB/s')
                    nic_write_column = row.index(interface+'-write-KB/s')

                elif row[0] == 'ZZZZ': # this line starts measure and tells time of it
                    if current_data is not None:
                        data_list.append(current_data)
                    current_data = System_Data(hostname)
                    current_time = time.strptime(row[2] + row[3], '%H:%M:%S%d-%b-%Y')
                    current_data.unixtime = time.mktime(current_time) #convert to unix epoch
                    index += 1

                elif row[0] == cpu_header: # Physical cpu times
                    try:
                        if int(row[1][1:]) == index:
                            current_data.cpu_usertime = float(row[2])
                            current_data.cpu_systime = float(row[3])
                    except ValueError: #only supposed to happen once
                        #print('value error')
                        continue

                elif row[0] == 'NET': # network load
                    try:
                        if int(row[1][1:]) == index:
                            current_data.network_read = float(row[nic_read_column]) * 1024
                            current_data.network_write = float(row[nic_write_column]) * 1024
                    except ValueError:
                        print('Error reading the nmon data for {0}'.format(current_data))
                        continue
                    
            data_list.append(current_data)
            return data_list
   
def main(myIP, interface, DTN_Monitor):    
    if platform.system() == 'AIX':
        command_line = 'nmon -f -s 1 -c {0} -d'.format(nmon_period)
    elif platform.system() == 'Linux':
        command_line = 'nmon -f -s 1 -c {0}'.format(nmon_period)
    args = shlex.split(command_line)

    def killhandle(signum, frame):
        print('Sigterm received')
        sys.exit()            

    signal.signal(signal.SIGTERM, killhandle)
    
    #run nmon for a period
    while True:
        try:
            nmon_process = subprocess.Popen(args)
            out, err = nmon_process.communicate()
            time.sleep(nmon_period)
            nmon_analyser = Nmon_analyser(myIP, interface, DTN_Monitor)
            nmon_analyser.start()        
        except KeyboardInterrupt:
            break
    nmon_analyser.join()
    sys.exit()

if __name__ == "__main__":
    print(sys.argv)
    main(sys.argv[1], sys.argv[2],sys.argv[3])
