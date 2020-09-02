#!/bin/bash

high_pid=`ps h -o %cpu,pid -C java|sort -nr|head -n1|awk '{print $2}'`;\
if [[ ! $high_pid ]];then
    echo '没有找到java进程！';
    exit 1;
fi
high_tid=`ps h -Lo %cpu,lwp -p $high_pid|sort -nr|head -n1|awk '{print $2}'`;\
if [[ -e "$1" ]];then
    jstack $high_pid | tee "$1" | grep -zoP '(?m)^"[^"]+".+'$(printf "0x%x" $high_tid)'[^"]+'
else
    jstack $high_pid | grep -zoP '(?m)^"[^"]+".+'$(printf "0x%x" $high_tid)'[^"]+'
fi
