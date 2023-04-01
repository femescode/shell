#!/bin/bash

while sleep 1; do
    now_time=$(date +%F_%H-%M-%S)
    pid=`ps h -o pid --sort=-pmem -C java|head -n1|xargs`;
    [[ ! $pid ]] && { unset n pre_fgc; sleep 1m; continue; }
    data=$(jstat -gcutil $pid|awk 'NR>1{print $4,$(NF-2)}');
    read old fgc <<<"$data";
    echo "$now_time: $old $fgc";
    if [[ $(echo $old|awk '$1>80{print $0}') ]]; then
        (( n++ ))
    else
        (( n=0 ))
    fi
    if [[ $n -ge 3 || $pre_fgc && $fgc -gt $pre_fgc && $n -ge 1 ]]; then
        jstack $pid > /home/work/logs/applogs/jstack-$now_time.log;
        if [[ "$@" =~ dump ]];then
            jmap -dump:format=b,file=/home/work/logs/applogs/heap-$now_time.hprof $pid;
        else
            jmap -histo $pid > /home/work/logs/applogs/histo-$now_time.log;
        fi
        { unset n pre_fgc; sleep 1m; continue; }
    fi
    pre_fgc=$fgc
done
