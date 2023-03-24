#!/bin/bash

while sleep 1; do
    pid=`ps h -o pid --sort=-pmem -C java|head -n1|xargs`;
    [[ ! $pid ]] && { n=0; pre_fgc=''; sleep 1m; continue; }
    data=$(jstat -gcutil $pid|awk 'NR>1{print $4,$(NF-2)}');
    now_time=$(date +%Y_%m_%dT%H_%M_%S)
    echo "$now_time:$data";
    read old fgc <<<"$data";
    if [[ $(echo $old|awk '$1>80{print $0}') ]]; then
        (( n++ ))
    else
        n=0
    fi
    if [[ $n -ge 3 || $pre_fgc && $fgc -gt $pre_fgc ]]; then
        jstack $pid > /home/work/logs/applogs/jstack_$now_time.log;
        jmap -histo $pid > /home/work/logs/applogs/histo_$now_time.log;
        { n=0; pre_fgc=''; sleep 1m; continue; }
    fi
    pre_fgc=$fgc
done
