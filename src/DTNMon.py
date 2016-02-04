#!/usr/bin/python
#comment : This module runs a DTN monitoring server to receive system records from the client
# and write to the output in result directory

import TransferMon, time, socket, threading, os, signal, sys, datetime
from nmon_analyser import System_Data
from FlowMon import Flow
import cPickle as pickle

# data structure for system information and flow information
class System_Records:
    def __init__(self, address):
        self.address = address
        self.flows = []
        self.system_data = []

    def update_flows(self,flows):
        for flow in flows:
            self.flows.append(flow)

    def update_system_data(self,system_data):
        for system_record in system_data:
            self.system_data.append(system_record)

# Flow table for maintaining flow data and watching traffic to signal low transfer rate
class FlowTable:

    def __init__(self):
        self.flow_table = []
        self.two_way_flow_table = []
        self.timeout = 180 #TCP session timeout


    def update(self, new_flow):
        flow_found = False

        for flow in self.flow_table: # remove existing flow with timeout
            if time.time() - flow.time > self.timeout:
                print("[{1}]\ttimeout for flow {0}".format(flow,time.time()))
                self.flow_table.remove(flow)
                for transfer_flows in self.two_way_flow_table:
                    if transfer_flows[0] is flow or transfer_flows[1] is flow:
                        self.two_way_flow_table.remove(transfer_flows)
                        print('two-way flow has become one-way')

        for flow in self.flow_table:
            if flow.match_flow(new_flow): #updating exsiting flow
                flow = new_flow
                #print('updated flow')
                flow_found = True
                break

        if flow_found: #updating exsiting  two way flow
            for flows in self.two_way_flow_table:
                if flows[0].match_flow(new_flow):
                    flows[0] = new_flow
                    #print('updating exsiting  two way flow')
                    return
                elif flows[1].match_flow(new_flow):
                    flows[1] = new_flow
                    #print('updating exsiting  two way flow')
                    return

        else: # if flow is not in our flow table, add the flow
            self.flow_table.append(new_flow)

            for flow in self.flow_table: # if there is flow that other way, then
                #this is flow makes it two-way flow
                if new_flow.source_IP == flow.dst_IP and new_flow.dst_IP == flow.source_IP:
                    print('[{0}]\tnew two-way flow found'.format(time.time()))
                    self.two_way_flow_table.append([flow,new_flow])
                    return

    def remove(self, srcIP): # removing flow from flow table
        for flow in self.flow_table:
            if flow.source_IP == srcIP:
                self.flow_table.remove(flow)

        for flows in self.two_way_flow_table:
            if flows[0].source_IP == srcIP or flows[0].dst_IP == srcIP:
                self.two_way_flow_table.remove(flows)

    def __str__(self):
        output = 'flow-table:\n'
        for flow in self.flow_table:
            output+= str(flow) + '\n'
        output+='two-way:\n'
        for transfer_flow in self.two_way_flow_table:
            output+= '{0}\n{1} \n'.format(transfer_flow[0],transfer_flow[1])
        return output

# Thread logging flow and system data to output
class Data_Logger (threading.Thread): 
    def __init__(self,system_records,lock,path):
        threading.Thread.__init__(self)
        self.system_records = system_records
        self.lock = lock
        self.path = path

    def run(self):
        curr_time = datetime.datetime.now().strftime('/%Y-%m-%d/')
        self.path += curr_time

        if not os.path.exists(self.path): os.makedirs(self.path)
        
        with self.lock:
            self.write_output()

    def write_output(self):
        new_file = False

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        total_flows = []

        for system in self.system_records: #writing system information to file
            if not os.path.isfile('{0}/{1}'.format(self.path,system.address)):
                    new_file = True
            log_file = open('{0}/{1}'.format(self.path,system.address),'a')
            if new_file:
                log_file.write('Machine name, Recorded time,'
                           'network socket read, network socket write, CPU user time,'
                           'CPU system time\n')
                new_file = False
                print('[{1}]\topening file {0}'.format(system.address,time.time()))

            for system_record in system.system_data:
                st = system_record.unixtime
                log_file.write('{0}, {1}, {2}, {3}, {4}, {5}\n'
                               ''.format(system_record.hostname,
                                         time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(system_record.unixtime)),
                                         system_record.network_read,
                                         system_record.network_write,
                                         system_record.cpu_usertime,
                                         system_record.cpu_systime))
            total_flows += system.flows
            system.system_data = []
            system.flows = []

        if not os.path.isfile('{0}/{1}'.format(self.path,'transfer.log')):
            new_file = True

        log_file = open('{0}/{1}'.format(self.path,'transfer.log'),'a')
        print('[{1}]\topening file {0}'.format('transfer.log',time.time()))
        if new_file:
            log_file.write('{0},{1},{2},{3}\n'.format('Time of transfer',
                                                      'Sender IP','Receiver IP',
                                                      'Goodput (Mb/s)'))
            new_file = False

        for flow in total_flows: # writing flow information to file
            if flow.number >= 0 and flow.transfer_size > 0 :
                print('[{1}]\t total flows : {0} written'.format(flow,time.time()))
                log_file.write('{0},{1},{2},{3}\n'.format(
                    time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(flow.time)),
                    flow.source_IP,flow.dst_IP, flow.transfer_size))
        log_file.close()
        
def register(flows,flow_table): # registering flows to flow table

    for flow in flows:
        if flow.number < 0:
            flow_table.remove(flow.source_IP)
            print('[{1}]\ttransfer_finished'.format(time.time()))
        else:
            flow_table.update(flow)


def main():
    flow_table = FlowTable()
    system_records = []
    var_lock = threading.Lock()
    log_path = './result'

    try:
        
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('', 50000))
        print('[{0}]\tlistening'.format(time.time()))
        serversocket.listen(5)

        def killhandle(signum, frame):
            print('Sigterm received')
            serversocket.close()
            sys.exit()            

        signal.signal(signal.SIGTERM, killhandle)

        while 1:
            #accept connections from outside
            (clientsocket, address) = serversocket.accept()
            print("[{0}]\tconnected to {1}".format(time.time(),address))
            data = clientsocket.makefile("r")
            result = pickle.loads(data.read())
            #results[0] always have IP, followed by data

            # if we received flow data, update flow table and record it into system_record
            if isinstance(result[1],Flow):
                print('[{1}]\tflow data received from {0}'.format(result[0],time.time()))
                ipaddr = result[0]
                register(result[1:],flow_table)

                #check IP address of the agent and use the address to record it into system record
                with var_lock:                    
                    system_to_update = None
                    for system_record in system_records:
                        if system_record.address == ipaddr:
                            system_to_update = system_record

                    if system_to_update == None:
                        system_to_update = System_Records(ipaddr)
                        system_records.append(system_to_update)
                
                    system_to_update.update_flows(result[1:])

            # if we received system data, record it into system_record
            elif isinstance(result[1],System_Data):
                print('[{1}]\tnmon data received from {0}'.format(result[0],time.time()))
                ipaddr = result[0]

                #check IP address of the agent and use the address to record it into system record
                with var_lock:
                    system_to_update = None
                    for system_record in system_records:
                        if system_record.address == ipaddr:
                            system_to_update = system_record

                    if system_to_update == None:
                        system_to_update = System_Records(ipaddr)
                        system_records.append(system_to_update)
                    
                    system_to_update.update_system_data(result[1:])                        

            else:
                pass

            clientsocket.close()
            print('[{0}]\tstarting data logger'.format(time.time()))
            data_logger = Data_Logger(system_records,var_lock,log_path)
            data_logger.start()
            
    except KeyboardInterrupt:
        print('[{0}]\tclosing down threads'.format(time.time()))
        serversocket.close()
        sys.exit()

if __name__ == "__main__":
    main()
