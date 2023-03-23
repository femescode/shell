#!/bin/bash

while true; do
    pid=`ps h -o pid --sort=-pmem -C java|head -n1|xargs`;
    old=$(jstat -gcutil $pid 500 2|awk 'NR>1{print $4}');
    echo $old;
    pct=$(echo "$old"|awk '$1>70{n++} END{if(n==NR)print $1}');
    if [[ $pct ]]; then
        jstack $pid > /home/work/logs/applogs/jstack.log; 
        jmap -histo $pid > /home/work/logs/applogs/histo.log; 
        break;
    fi
done
