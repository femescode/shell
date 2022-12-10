#!/bin/bash

if [[ ! $@ =~ "-s" ]]; then
    # 时间范围内活跃过的连接
    b="${1:-0}"
    e="${2:-2000}"
    ss -natpeoi | sed '1!{N;s/\n//;}' | awk -v b=$b -v e=$e ' match($0,/lastsnd:([0-9]+)/,a) && a[1]>b && a[1]<e'
else
    # 连接在活跃时间上的分布
    ss -nati | sed '1!{N;s/\n//;}' | awk ' 
    match($0,/lastsnd:([0-9]+)/,a) { 
        k=int(log(a[1])/log(2)); 
        S[k][$1]++ 
    } 
    END{ 
        PROCINFO["sorted_in"] = "@ind_num_asc"; 
        for(k in S){ 
            printf ">%-15s ",2^k"ms"; 
            for(state in S[k]){ 
                printf "%s(%s) ",state,S[k][state] 
            } 
            print "" 
        } 
    }'
fi

