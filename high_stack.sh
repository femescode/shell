#!/bin/bash

high_pid=`ps h -o %cpu,pid -C java|sort -nr|head -n1|awk '{print $2}'`;\
high_tid=`ps h -Lo %cpu,lwp -p $high_pid|sort -nr|head -n1|awk '{print $2}'`;\
jstack $high_pid | tee thread.log | grep -zoP '(?m)^"[^"]+".+'$(printf "0x%x" $high_tid)'[^"]+'
