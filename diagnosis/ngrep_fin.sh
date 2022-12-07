#!/bin/bash

if [[ $# -lt 1 || $@ =~ '-h' || $@ =~ '--help' ]]; then
    echo -e "Trace peer side active close tcp connection." >&2
    echo -e "Usage: bash ngrep_fin.sh 'tcp and port 80' 80" >&2
    exit 1
fi

ngrep -l -t -d any -W single '' "$1" | awk -v port="${2:-80}" '
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
    # print "in:" (max_idx+1) "\t" item
    if(length(arr) > limit){
        if(min_idx > 0){
            # print "delete:" min_idx "\t" arr[min_idx]
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
        if($7 !~ /F/){
            append(cmap[key], $0, 2)
        }else{
            delete cmap[key]
        }
    }else{
        key = $6 "-" $4
        cmap[key][0]=0
        delete cmap[key][0]
        if($7 !~ /F/){
            append(cmap[key], $0, 2)
        }else{
            if(length(cmap[key])>0){
                print "peer close"
                sb=""
                PROCINFO["sorted_in"] = "@ind_num_asc";
                for(i in cmap[key]){
                    sb = sb "\n" cmap[key][i]
                    last = cmap[key][i]
                }
                if(last !~ /Connection: close/){
                    print sb
                    print $0
                    fflush()
                    exit(0)
                }
            }
            delete cmap[key]
        }
    }
}' 