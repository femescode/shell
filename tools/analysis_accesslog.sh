#!/bin/bash

extract_fields(){
    awk -v FPAT='[^"\\\\ \\[\\]]+|"[^"]*"|\\[[^\\]]+\\]' '
    function strptime(str,     time_str,arr,Y,M,D,H,m,S){
        time_str = gensub(/[\/:]+/, " ", "g", str)
        split(time_str, arr, " ")
        Y = arr[3]
        M = month_map(arr[2])
        D = arr[1]
        H = arr[4]
        m = arr[5]
        S = arr[6]
        return mktime(sprintf("%d %d %d %d %d %d", Y,M,D,H,m,S))
    }
    function month_map(str,   mon){
        mon["Jan"] = 1
        mon["Feb"] = 2
        mon["Mar"] = 3
        mon["Apr"] = 4
        mon["May"] = 5
        mon["Jun"] = 6
        mon["Jul"] = 7
        mon["Aug"] = 8
        mon["Sep"] = 9
        mon["Oct"] = 10
        mon["Nov"] = 11
        mon["Dec"] = 12
        return mon[str]
    }
    {
        timestamp=strptime(gensub(/[\[\]]+/, "", "g", $4))
        req_time=strftime("%dT%H:%M", timestamp)
        split($5, req_arr, /\s+/)
        split(req_arr[2], url_arr, /\?/)
        req_url=url_arr[1]
        req_cost=$7
        printf "%s %s %s\n",req_time,req_url,req_cost
    }'
}

analysis_data(){
    awk -v mt=${1:-0} '
    $3 >= mt {
        T[$1]++; 
        URL[$2]++; 
        URL_T[$2,$1]++
    } 
    END{
        # 打印标题行
        printf "url"
        for(t in T){
            printf " %s",t
        }
        printf "\n"
        # 打印汇总数据
        printf "total";
        for(t in T){
            printf " %s",T[t]
        }
        printf "\n"
        # 打印数据
        for(u in URL){
            printf u;
            for(t in T){
                printf " %s",URL_T[u,t]?URL_T[u,t]:0
            }
            printf "\n"
        }
    }'
}

extract_fields | analysis_data "$1" | column -t |less -iSFX
