#!/bin/bash

pid="$1"
[[ ! "$pid" ]] && { pid=`ps h -o pid --sort=-pmem -C java|head -n1`; }
[[ ! "$pid" ]] && { echo "not found java process, usage: $0 pid" >&2; exit 1; }

strace -T -ttt -e trace=network -f -s 200 -p $pid|& tee strace.log | awk '
    match($0, /(\S+) (\S+) sendto\(\w+, "(.|\\\w+){4}\\3([^"]+)"/, a) { 
        ts[a[1]]=a[2];
        sql[a[1]]=a[4] 
    } 
    match($0, /(\S+) (\S+) \W*recvfrom.+ <([0-9\.]+)>/, b) && ts[b[1]] { 
        printf "%6s %.2fms %s->%s %s\n",b[1],(b[2]-ts[b[1]])*1000,ts[b[1]],b[2],sql[b[1]];
        delete ts[b[1]];
        delete sql[b[1]] 
    }'
