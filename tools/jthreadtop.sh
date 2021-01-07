#!/bin/bash

pid=`ps h -o %cpu,pid -C java|sort -nr|head -n1|awk '{print $2}'`;\
if [[ ! $pid ]];then
    echo '没有找到java进程！' >&2;
    exit 1;
fi
tlist=$(ps h -Lo %cpu,lwp,comm -p $pid|sort -nr|awk 'BEGIN{printf "nid\tcpu\ttid\tcomm\n"}NR<=10{printf "0x%x\t%s\n",$2,$0}')
tid=$(echo "$tlist"|awk 'NR==2{print $3}')
logfile="jstack_$(date +%Y%m%dT%H%M%S)_"$pid"_$tid.log"
ps -fp $pid > $logfile
printf "\nPID: %s\n\nTop thread list:\n%s\n\n" $pid "$tlist" >> $logfile
jstack $pid 2>&1 >> $logfile
cat $logfile|awk -v RS="" -v tid=$tid 'BEGIN{nid=sprintf("0x%x",tid)} match($0,nid)'
