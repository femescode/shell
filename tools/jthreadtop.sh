#!/bin/bash

pid="$1"
[[ ! "$pid" ]] && { pid=`ps h -o pid --sort=-pmem -C java|head -n1`; }
[[ ! "$pid" ]] && { echo 'not found java process, usage: $0 pid num' >&2; exit 1; }
jstacklog=$(mktemp)
jstack $pid 2>&1 > "$jstacklog"
top -d 0.5 -b -n2 -H -p $pid |awk -v RS= '{s=$0}END{print s}'|awk '!/PID/{printf "%s 0x%x\n",$9,$1}'|sort -nrk1|head -n10|(
    while read cpu nid;do
        echo -n "$cpu "
        cat "$jstacklog"|awk -v RS= -v nid="$nid" 'match($0, nid)' && echo
    done
)
rm "$jstacklog"
