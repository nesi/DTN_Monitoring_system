#!/usr/bin/env python
#comment : watching netstat each second to check if gridftp is running. If it is,
# get the transfer rate by looking at the file size difference and 5 tuples from
#netstat command

import commands, time, socket, json, TransferMon, platform, sys, signal
import cPickle as pickle

#data structure for Flow information
class Flow:
    def __init__(self, pid,src, srcpt, dst, dstpt):
	self.pid = pid
	self.number = 0
        self.source_IP = src
        self.source_port = int(srcpt)
        self.dst_IP = dst
        self.dst_port = int(dstpt)
        self.transfer_size = 0
        self.time = time.time()
        
    #check whether two flows have the same 5 tuple information
    def match_flow(self, new_flow):
        if (self.source_IP  == new_flow.source_IP and
            self.source_port == new_flow.source_port and
            self.dst_IP == new_flow.dst_IP and
            self.dst_port == new_flow.dst_port):
            return True
        return False
    
    def __str__(self):
        return('{5} - {0}:{1} <-> {2}:{3} : {4}'.format(self.source_IP,self.source_port,
        self.dst_IP,self.dst_port, self.transfer_size,self.number))

#update flow number as transfer flow found and appended
class Flow_Counter:
    def __init__(self):
        self.flows = []
        
    def update_flow_number(self, new_flow):
        index = 0
        for flow in self.flows:            
            if flow.match_flow(new_flow):
                flow.number += 1
                new_flow.number = flow.number
                return
            index += 1

        flow_copy = Flow('0',new_flow.source_IP, new_flow.source_port,new_flow.dst_IP, new_flow.dst_port )
        self.flows.append(flow_copy)
            
#check netstat output and create flow objects from the output
def parse_netstat_output(myIP,netstat_line):
    
    if platform.system() == 'AIX':
        index_to_extract = [0,4,5] #src, dst
        flows_info = [netstat_line.split()[i] for i in index_to_extract]
        
        try:
            pid = commands.getstatusoutput('rmsock ' + flows_info[0] +
                                       ' tcpcb')[1].split()[8]
        except IndexError:
            print('error : rmsock {0} tcpcb'.format(flows_info[0]))
            pid = 0
        src,srcpt = [myIP,flows_info[1].rsplit('.',1)[1]]
        dst, dstpt = flows_info[2].rsplit('.',1)
        flow = Flow(pid,src,srcpt,dst,dstpt)
        
    elif platform.system() == 'Linux':
        index_to_extract = [0,3,4] #src, dst    
        flows_info = [netstat_line.split()[i] for i in index_to_extract]
        
	pid = '0'
        src,srcpt = [myIP,flows_info[1].split(':')[1]]
        dst, dstpt = flows_info[2].split(':')        
        flow = Flow(pid,src,srcpt,dst,dstpt)

    return flow

# Check if flow is already in the transfer flows, and insert if not in the transfer flows yet
def insert_transfer_flow(flow, transfer_flows,transfer_monitor):
    found = False

    for transfer_flow in transfer_flows:
        if transfer_flow.source_IP == flow.source_IP and transfer_flow.dst_IP == flow.dst_IP:
            found = True

    if not found: # if the flow is not in the flow table for transfer, insert to the flow table
        file_transferred = transfer_monitor.get_size_diff()
        flow.transfer_size = file_transferred /1024 /1024
        transfer_flows.append(flow)
        #print('Transfer with {0} found'.format(flow.dst_IP))

# Get all flows from netstat, identify if it is a transfer flow and insert into transfer flow table
def watch_Flow(myIP,DTNs,transfer_monitor,flow_counter):
    transfer_found = False
    flows = []
    transfer_flows = []

    if platform.system() == 'AIX':
        sockets = commands.getstatusoutput('netstat -aAn')
    else:
        sockets = commands.getstatusoutput('netstat -an')

    for socket in sockets[1].split('\n'): # get list of connected sockets from netstat
        if 'ESTABLISHED' in socket and 'tcp' in socket:
            try:
                flows.append(parse_netstat_output(myIP,socket))
            except ValueError:
                print('error on decrypting line {0}'.format(socket))
            
    for flow in flows: # parse sockets into flow objects
        if (flow.dst_IP in DTNs and flow.source_port > 50000 and flow.source_port < 51000
        and flow.dst_port > 50000 and flow.dst_port < 51000):
            flow_counter.update_flow_number(flow)
            insert_transfer_flow(flow, transfer_flows,transfer_monitor)
            transfer_found = True    
    
    if not transfer_found: # if there is no transfer found, make an empty flow
        flow = Flow(None,myIP,0,None,0)
        flow.number = -1
        insert_transfer_flow(flow,transfer_flows,transfer_monitor)

    return [transfer_found,transfer_flows]
    
def main(myIP,TRANSFER_DESITNATION,DTN_Monitor,DTNs):
    ongoing_transfer = False

    buffer = [myIP]
    counter = 0

    flow_counter = Flow_Counter()
    
    transfer_monitor = TransferMon.TransferMon(TRANSFER_DESITNATION)
    prev_time = time.time()

    try:
        while 1:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            def killhandle(signum, frame):
                print('Sigterm received')
                s.close()
                sys.exit()
                

            signal.signal(signal.SIGTERM, killhandle)
            
            current_time=time.time() 
            if current_time - prev_time < 1: # run once within a sec
                time.sleep(1.0 - (current_time - prev_time))
            prev_time = time.time()

            transfer_found,transfer_flows = watch_Flow(myIP,DTNs,transfer_monitor,flow_counter)
                
            if transfer_found: # if there is a transfer going on, report the information every minute
                if not ongoing_transfer:
                    print("[{0}]\tTransfer started".format(time.time()))
                    ongoing_transfer = True

                for flow in transfer_flows:
                    print(flow)
                    buffer.append(flow)

                if counter >= 60: #update table every minute                    
                    s.connect((DTN_Monitor, 50000))            
                    s.send(pickle.dumps(buffer, -1))
                    s.close()
                    print('[{0}]\tflows sent'.format(time.time()))
                    buffer = [myIP]
                    counter = 0
                    
            elif ongoing_transfer: # if transfer finishes, report the information immediately
                for flow in transfer_flows:
                    buffer.append(flow)
                print("[{0}]\tTransfer finished".format(time.time()))
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((DTN_Monitor, 50000))            
                s.send(pickle.dumps(buffer, -1))            
                s.close()
                print('[{0}]\tflows sent'.format(time.time()))
                buffer = [myIP]
                ongoing_transfer = False
                
            counter += 1
    except KeyboardInterrupt:
        print('[{0}]\tclosing down threads for FlowMon'.format(time.time()))
        sys.exit()


if __name__ == "__main__":
    #print(sys.argv)
    main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4:])
