#!/bin/bash

pid="$1"
[[ ! "$pid" ]] && { pid=`ps h -o pid --sort=-pmem -C java|head -n1`; }
[[ ! "$pid" ]] && { echo "not found java process, usage: $0 pid" >&2; exit 1; }

strace -T -tt -f -s 200 -p $pid|& tee strace.log | awk '
    function print_res(){
        for(key in callnum){
            split(key,k,SUBSEP);
            printf "%s %24s %6s %.6f \n",k[1],k[2],callnum[key],sumtime[key]
        }
        print "";
        delete sumtime;
        delete callnum;
    }
    { t=systime(); if(!pt){pt=t}; if(t-pt>=1){print_res();pt=t} }
    match($0,/(\S+) (\S+)\.\w+ (.+) = ([0-9\.-]+) .*<([0-9\.]+)>/,o){
        match(o[3],/^(\w+)/,name)||match(o[3],/^<\.\.\.\s+(\S+)/,name);
        if(!name[1])print $0,o3
        sumtime[o[2],name[1]]+=o[5];
        callnum[o[2],name[1]]++
    }
    END{
        print_res();
    }'
