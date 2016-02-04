#!/usr/bin/env python
#author : Se-young Yu
#
#comment: This module calculate file sizes of the path given and return difference of the
#file size each time they run get_size_diff()

import os,  commands, platform

class TransferMon:
    #get initial file sizes for data storage
    def __init__(self,path):
        self.path = path
        self.file_sizes = dict()
        self.istransfer= False
        for (dirpath, dirnames, filenames) in os.walk(self.path):
            for filename in filenames:
                full_path = os.sep.join([dirpath, filename])
                if platform.system() == 'AIX':                
                    self.file_sizes[full_path] = int(commands.getstatusoutput('ls -l ' + full_path)[1].split(' ')[7])
                elif platform.system() == 'Linux':
                    self.file_sizes[full_path] = os.path.getsize(full_path)
        
    #return size difference of the path between current and the last time this function is called
    def get_size_diff(self):        

        file_size_change = 0
        
        for (dirpath, dirnames, filenames) in os.walk(self.path):
            for filename in filenames:                
                full_path = os.sep.join([dirpath, filename])
                if platform.system() == 'AIX':
                    file_size = int(commands.getstatusoutput('ls -l ' + full_path)[1].split(' ')[7])
                elif platform.system() == 'Linux':
                    file_size = os.path.getsize(full_path)                   
                
                if full_path in self.file_sizes:
                    difference = file_size - self.file_sizes[full_path]
                    if difference < 0:
                        difference = file_size
                else:
                    difference = file_size
                    
                file_size_change += difference                
                self.file_sizes[full_path] = file_size
        
        if file_size_change > 1000000000 and not self.istransfer: # remove false size when recreating file
            file_size_change = 0
            self.istransfer = true
        return file_size_change
            


