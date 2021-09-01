#!/bin/bash

pid="$1"
if [[ ! "$pid" ]];then
    pid=$(ps h -o %cpu,pid -C java|sort -nr|head -n1|awk '{print $2}')
fi
if [[ ! "$pid" ]];then
    echo '没有找到java进程, usage: jthreadtop pid' >&2;
    exit 1;
fi
jstacklog=$(mktemp)
jstack $pid 2>&1 > "$jstacklog"
ps h -Lo %cpu,lwp,comm -p $pid|sort -nr|head -n10|(
    while read cpu tid comm;do
        nid=$(printf "0x%x" $tid)
        printf "%-10s " "tid:$tid" "cpu:$cpu" "nid:$nid" "comm:$comm" && echo
        cat "$jstacklog"|awk -v RS= -v nid="$nid" 'match($0, nid)' && echo
    done
)
rm "$jstacklog"
