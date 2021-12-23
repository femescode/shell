#!/bin/bash

pid="$2"
[[ ! "$pid" ]] && { pid=`ps h -o pid --sort=-pmem -C java|head -n1`; }
[[ ! "$pid" ]] && { echo "not found java process, usage: $0 num pid" >&2; exit 1; }
jstacklog=$(mktemp -p . jstack_XXXXXXXXXX.log)

num="${1:-10}"
for i in `seq $num`;do 
    jstack $pid; 
    sleep 0.2; 
done > $jstacklog

cat $jstacklog|sed -E -e 's/0x[0-9a-z]+/0x00/g' -e '/^"/ s/[0-9]+/n/g' \
    |awk -v RS="" 'gsub(/\n/,"\\n",$0)||1' \
    |sort|uniq -c|sort -nr \
    |sed 's/$/\n/;s/\\n/\n/g' \
    |less

