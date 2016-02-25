#comment: This module analyse output of the DTN monitor and generate plot
#author : Se-young Yu
#Date : 02/26/2016

import matplotlib.pyplot as plt
import datetime
from numpy import genfromtxt, mean, sum
from matplotlib import dates
from os import listdir

# parse date string to datetime object
def with_indexing(dstr):
    dstr= dstr.strip()
    return datetime.datetime(*map(int, [dstr[:4], dstr[5:7], dstr[8:10],
                                        dstr[11:13], dstr[14:16], dstr[17:]])) 
# convert byte to MB
def to_MB(byteval):
    return float(byteval)/1024/1024

# covert time_interval to total second for python < 2.6
def total_seconds_py26(time_d):
    return (time_d.days * 86400) + time_d.seconds

# draw plot from the system data and transfer data
def draw(data,time_data,title,transfers, path):    
    sample_sec = 20
    
    transfer_times = []
    goodputs = []
    curr_date = None
    buffer = []

    # for each transfer data, get the mean of the each cluster with sample_sec
    for transfer in transfers:
        transfer_time = with_indexing(transfer.split(',')[0])        
        if curr_date is None:
            curr_date = transfer_time
            buffer.append(float(transfer.split(',')[-1]))
        elif total_seconds_py26(transfer_time - curr_date) < sample_sec:
            buffer.append(float(transfer.split(',')[-1]))
        else: # Get mean of sample and append to the measures
            diff = total_seconds_py26(transfer_time - curr_date)
            if diff > (2* sample_sec): # pad 0 transfer rate to the records which left out from flow_mon reports
                transfer_times.append(curr_date + datetime.timedelta(0,10))
                goodputs.append(0)
                if diff > (3*sample_sec):                    
                    transfer_times.append(transfer_time - datetime.timedelta(0,10))
                    goodputs.append(0)                               
            
            transfer_times.append(transfer_time)
            goodputs.append(sum(buffer)/diff)
            buffer = []
            curr_date = None
    

    #prepare plot meta-data
    fig1, ax1 = plt.subplots()

    formatter =  dates.DateFormatter('%H:%M:%S')
    plt.gcf().axes[0].xaxis.set_major_formatter(formatter)

    fig1.autofmt_xdate()    
    fig1.suptitle(filename + ' CPU and Network load', fontsize=30, fontweight='bold')
    ax1.set_title('')
    ax1.tick_params(labelsize=30)
    
    # sampling mean of n element from the raw data to make it eaiser to read in plot
    socket_read_data = mean(data[:,0].reshape(-1, sample_sec), axis=1)
    socket_write_data = mean(data[:,1].reshape(-1, sample_sec), axis=1) 

    #plotting socket read, write and transfer rate
    socket_read = ax1.plot(time_data[::sample_sec], socket_read_data,'r',label="Socket read",linewidth=3.0)
    socket_write = ax1.plot(time_data[::sample_sec], socket_write_data,'b', label="Socket write",linewidth=3.0)
    transfer_rate = ax1.plot(transfer_times, goodputs,'m', label="Transfer rate" , linewidth=3.0)
    ax1.set_ylabel('TCP socket bytes (MB/s)',fontsize=30)

    #plotting cpu times using y2 axis
    ax2 = ax1.twinx()
    ax2.tick_params(labelsize=30)
    
    cpu_user_data = mean(data[:,2].reshape(-1, sample_sec), axis=1)
    cpu_sys_data = mean(data[:,3].reshape(-1, sample_sec), axis=1)
    cpu_user = ax2.plot(time_data[::sample_sec], cpu_user_data,'g--',label="CPU user load",linewidth=3.0)
    cpu_sys = ax2.plot(time_data[::sample_sec], cpu_sys_data,'c--',label="CPU system load",linewidth=3.0)    
    ax2.set_ylim(bottom =0, top = 100)
    ax2.set_ylabel('CPU load (%)',fontsize=30)
    
    lns = socket_read + socket_write +transfer_rate + cpu_user + cpu_sys
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc=1)
    
    fig = plt.gcf()
    fig.set_size_inches(20, 10)
    fig1.savefig(path + '/' + filename + '.pdf', format='pdf',dpi=100)

# parse the data file and call draw function to draw plot
if __name__ == '__main__':

    transferfile ='transfer.log'         
    resultdir = 'result'

    folders = listdir(resultdir)
    print('please choose the date to plot')
    counter = 0
    for folder in folders:
        print('{0}. {1}'.format(counter, folder))
        counter += 1
    print('a. all of above')

    selection = raw_input()
    #selection = input()
    
    if selection == 'a':
        pass
    else:
        folders = [folders[int(selection)]]

    # for each selected date folders, generate a list of datetime object and float for measured data    
    for folder in folders:
        print('reading {0}/{1}/{2}'.format(resultdir,folder,transferfile))

        # first read transfer flow data
        with open('{0}/{1}/{2}'.format(resultdir,folder,transferfile), 'r') as f:
            transfers = f.read()

        # then read system data from the selected folder
        for filename in listdir('{0}/{1}/'.format(resultdir,folder)):
            if filename == transferfile or str(filename).endswith('.pdf'): continue
            print('reading {0}/{1}/{2}'.format(resultdir,folder,filename))
            my_data = genfromtxt('{0}/{1}/{2}'.format(resultdir,folder,filename), delimiter=',', usecols = (2,3,4,5),
                                 skip_header=1,converters={2:to_MB, 3:to_MB})
            time_data = genfromtxt('{0}/{1}/{2}'.format(resultdir,folder,filename), delimiter=',', usecols = (1),
                                   skip_header=1,converters={1:with_indexing})
             
            matched_lines = [line for line in transfers.split('\n') if filename in line]
            draw(my_data,time_data,filename,matched_lines, resultdir+'/' + folder)
