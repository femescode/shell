#!/bin/bash

extract_fields(){
    awk -v mt=${1:-0} '
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
    int($11) >= mt{
        timestamp=strptime(substr($4,2))
        req_time=strftime("%dT%H:%M", timestamp)
        split($7, url_arr, /\?/)
        req_url=url_arr[1]
        req_cost=int($11)
        printf "%s %s %s\n",req_time,req_url,req_cost
    }'
}

analysis_data(){
    awk '
    $3 >= mt {
        T[$1]++; 
        URL[$2]++; 
        URL_T[$2,$1]++
    } 
    END{
        asorti(T,sort_time_arr,"@ind_str_asc")
        asorti(URL,sort_url_arr,"@val_num_desc")
        # 打印标题行
        printf "time/url total"
        for(i in sort_url_arr){
            printf " %s",sort_url_arr[i]
            total += URL[sort_url_arr[i]]
        }
        printf "\n"
        # 打印汇总数据
        printf "total %s",total;
        for(i in sort_url_arr){
            printf " %s",URL[sort_url_arr[i]]
        }
        printf "\n"
        # 打印数据
        for(i in sort_time_arr){
            t=sort_time_arr[i]
            printf "%s %s",t,T[t];
            for(j in sort_url_arr){
                u=sort_url_arr[j]
                printf " %s",URL_T[u,t]?URL_T[u,t]:0
            }
            printf "\n"
        }
    }'
}

extract_fields "$1" | analysis_data | column -t |tee `mktemp -p . analysis_XXXXXXXXXX.txt`|less -iSFX
