#!/bin/bash

if [[ $# -lt 3 || $@ =~ '-h' || $@ =~ '--help' ]]; then
    echo -e "Trace match pattern packet and it before 2 packet." >&2
    echo -e "Usage: bash ngrep_with_before.sh 'tcp and port 80' 80 'HTTP/1.1 200'" >&2
    exit 1
fi

ngrep -l -t -d any -W single '' "$1" | awk -v port="${2:-80}" -v pat="$3" '
function append(    arr,item,limit){
    min_idx=0
    max_idx=0
    PROCINFO["sorted_in"] = "@ind_num_asc";
    for(i in arr){
        if(min_idx==0){
            min_idx=i
        }
        max_idx=i
    }
    arr[max_idx+1]=item
    # print "offer:" (max_idx+1) "\t" item
    if(length(arr) > limit){
        if(min_idx > 0){
            # print "pop:" min_idx "\t" arr[min_idx]
            delete arr[min_idx]
        }
    }
}
/^T /{
    split($4,s,":")
    split($6,d,":")
    if($7 ~ /\[A\]/){
        next
    }
    if(int(d[2]) == port){
        key = $4 "-" $6
        cmap[key][0]=0
        delete cmap[key][0]
        append(cmap[key], $0, 2)
    }else{
        key = $6 "-" $4
        cmap[key][0]=0
        delete cmap[key][0]
        if($0 !~ pat){
            append(cmap[key], $0, 2)
        }else{
            if(length(cmap[key])>0){
                print "get matched"
                sb=""
                PROCINFO["sorted_in"] = "@ind_num_asc";
                for(i in cmap[key]){
                    sb = sb ? (sb "\n" cmap[key][i]) : cmap[key][i]
                    last = cmap[key][i]
                }
                if(last !~ /Connection: close/){
                    print sb
                    print $0
                    print ""
                    fflush()
                }
            }
            delete cmap[key]
        }
    }
}' 