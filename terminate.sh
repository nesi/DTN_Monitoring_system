#!/bin/bash
pid_dtnmon=`ps aux|grep 'python -u src/DTN'|awk '{print $2}'`
kill $pid_dtnmon
pid_flowmon=`ps aux|grep 'python src/Flo'|awk '{print $2}'`
kill $pid_flowmon
pid_nmon=`ps aux|grep 'python src/nmo'|awk '{print $2}'`
kill $pid_nmon

pid_flowmon=`ps aux|grep 'python -u src/Flo'|awk '{print $2}'`
kill $pid_flowmon
pid_nmon=`ps aux|grep 'python -u src/nmo'|awk '{print $2}'`
kill $pid_nmon