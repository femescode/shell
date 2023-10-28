#!/bin/bash

stack_filter_collapsed() {
    script='
    /[0-9]{4}-[0-9]+-[0-9]+/{
        t=gensub(/\s/,"_","g",$1)
    } 
    t>=begin && t<=end && $0 ~ tname {
        cstack=""
        for(i=NF;i>=1;i--){
            if(match($i, /at\s+([0-9a-zA-Z.$]+)/,m)){
                cstack = cstack m[1] ";"
            }
        }
        cstack = cstack t;
        print cstack;
    }
    '
    awk -F'\n' -v RS= -v begin="$1" -v end="$2" -v tname="$3" "$script"
}

diff_lineno() {
    IFS=';'
    read -a stack_arr1
    read -a stack_arr2
    IFS=$'\n'
    diff <(echo "${stack_arr1[*]}") <(echo "${stack_arr2[*]}") | awk -F 'c' 'NR==1{print $1}' | cut -d, -f1
    unset IFS
}

color_diff() {
    while read -r num stack; do 
        if [[ ! "$old_stack" ]];then
            echo $num
            echo "$stack" | tr ';' '\n';
            echo
        else
            dno=$( (echo "$old_stack"; echo "$stack") | diff_lineno )
            echo $num
            i=1
            IFS=';' read -a stack_arr <<<"$stack"
            for frame in "${stack_arr[@]}"; do
                if [[ $dno && $i -eq $dno ]];then
                    echo -ne '\033[31m'
                fi
                echo "$frame"
                ((i++))
            done
            echo -e '\033[0m'
        fi
        old_stack="$stack"
    done
}

show_usage() {
    echo "Usage: jstack_extract -b '2023-10-13_22:17:01' -e '2023-10-13_22:17:02' -t 'http-nio-8080-exec-8' jstack.log " >&2
    echo "-b|--begin : the begin time to filter stack." >&2
    echo "-e|--end : the end time to filter stack." >&2
    echo "-t|--tname : the thread name to filter stack." >&2
}

while true ; do
    case "$1" in
        -b|--begin) begin="$2" ; shift 2 ;;
        -e|--end) end="$2" ; shift 2 ;;
        -t|--tname) tname="$2" ; shift 2 ;;
        --) shift ; break ;;
        -*) echo $1; show_usage ; exit 1 ;;
        *) break ;;
    esac
done

if [[ ! $begin || ! $end || ! $tname ]]; then
    show_usage ; exit 1
fi

cat "$1" | stack_filter_collapsed "$begin" "$end" "$tname" | uniq -c | color_diff