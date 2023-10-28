#!/bin/bash

show_usage() {
    echo "Usage: jstack_top [-n 4] [pid] " >&2
    echo "-n|--num : Display the specified number of threads." >&2
}

while true ; do
    case "$1" in
        -n|--num) num="$2" ; shift 2 ;;
        --) shift ; break ;;
        -*) echo $1; show_usage ; exit 1 ;;
        *) break ;;
    esac
done

pid="$1"
[[ ! "$pid" ]] && { pid=`ps h -o pid --sort=-pmem -C java|head -n1`; }
[[ ! "$pid" ]] && { echo "not found java process" >&2; exit 1; }

toptid_file=$(mktemp toptid_XXXXXXXXXX.log)
top -d 0.5 -b -n2 -H -p $pid |awk -v RS= 'END{print $0}'|awk '!/PID/{printf "%s 0x%x\n",$9,$1}'|head -n ${num:=4} > $toptid_file

jstacklog=$(mktemp jstack_XXXXXXXXXX.log)
jstack $pid > $jstacklog

while read -r cpu nid; do
    stack=$(awk -v RS= -v nid="$nid" '$0 ~ ("nid=" nid)' $jstacklog)
    echo "$cpu" "$nid" "$stack"
done < $toptid_file

rm $toptid_file
rm $jstacklog