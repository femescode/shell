#!/bin/bash

function jstackwithcpu(){
    pid=$1
    tidlist=$(top -d 0.5 -b -n2 -H -p $pid |awk -v RS= '{s=$0}END{print s}'|awk '!/PID/{printf "%s 0x%x\n",$9,$1}')
    stacklog=$(jstack $pid 2>&1)
    awk -v RS= -v ORS='\n\n' 'NR==FNR{s[$2]=$1} NR!=FNR{match($0,/nid=(\w+)/,a); printf "%s0 ::: %s\n\n",s[a[1]],$0}' <(echo "$tidlist") <(echo "$stacklog") 
    echo
}

pid="$1"
[[ ! "$pid" ]] && { pid=`ps h -o pid --sort=-pmem -C java|head -n1`; }
[[ ! "$pid" ]] && { echo 'not found java process, usage: $0 pid num' >&2; exit 1; }
jstacklog=$(mktemp)

num="${2:-10}"
for i in `seq $num`;do 
    jstackwithcpu $pid; 
    # sleep 0.2; 
done > $jstacklog

cat $jstacklog|sed -E -e 's/0x[0-9a-z]+/0x00/g' -e '/^[0-9.]+ ::: "/ s/[0-9]+/n/3g'|awk -v RS="" -v FS=":::" '{s[$2]["num"]++;s[$2]["cpu"]+=$1} END{for(k in s){cpu=s[k]["cpu"];num=s[k]["num"];printf "%-3s ::: %-3s ::: %3s\n\n",cpu,num,k}}'|awk -v RS="" -v FS=":::" 'gsub(/\n/,"\\n",$0)||1' |sort -nrk1|sed 's/$/\n/;s/\\n/\n/g'|less -S

rm "$jstacklog"
