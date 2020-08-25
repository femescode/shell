#!/usr/bin/env bash

function git-branch-name {
  git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3-
}
function git-branch-prompt {
  local branch=`git-branch-name`
  if [ $branch ]; then printf " [%s]" $branch; fi
}
PS1="\[\e]0;\w\a\]\n\[\e[01;32m\]\u@\h \[\e[33m\]\w\[\e[0m\] \[\033[0;36m\]\$(git-branch-prompt)\[\033[0m\] \n\$ "

#修改ll时间格式
export TIME_STYLE='+%Y-%m-%d %H:%M:%S'
alias ll='ls -lh'

epochformat(){
    if [[ $# > 0 ]];then
        "date" --date="@$@" +"%Y-%m-%d %H:%M:%S %z"
    else
        "date" +"%Y-%m-%d %H:%M:%S %z"
    fi
}
epoch(){
    if [[ $# > 0 ]];then
        "date" --date="$@" +%s
    else
        "date" +%s
    fi
}

dosbash(){
    args=()
    opts=()
    findfile=0
    for arg in "$@";do
        if [[ -e $arg || $arg == '-' ]];then
            findfile=1
        fi
        if [[ $findfile -eq 0 ]];then
            opts=("${opts[@]}" "$arg")
        else
            args=("${args[@]}" "$arg")
        fi
    done
    if [[ -e "${args[0]}" || "${args[0]}" == '-' ]];then
        data=$(cat "${args[0]}")
        unset args[0]
    else
        data=$(cat)
    fi
    bash "${opts[@]}" <(echo -n "$data"|dos2unix|mac2unix) "${args[@]}"
}


escape(){
    if [[ $1 ]];then
        cat $1|od -An -t a|tr -d "\n"|sed 's/nl/nl\n/g'
    else
        cat|od -An -t a|tr -d "\n"|sed 's/nl/nl\n/g'
    fi
}

urlencode() {
    local length="${#1}"
    for (( i = 0; i < length; i++ )); do
        local c="${1:i:1}"
        case $c in
            [a-zA-Z0-9.~_-]) printf "$c" ;;
            *) printf "$c"|xxd -p -c1|xargs printf "%%%s"
        esac
    done
}

ogrep ()
{
    while read line; do
        i=0;
        for reg in "$@";
        do
            ostr=$(grep <<< "$line" -oP "$reg");
            if [[ -n "$ostr" ]]; then
                printf "%s\t" "$ostr";
                i=$(($i+1));
            fi;
        done;
        [[ $i > 0 ]] && echo;
    done
}

underline2Camelcase(){
    pat='\w+(_\w+)+'
    sb=""
    IFS="\n"
    while read -r line;do
        let pre_end=0;
        while read -r cw;do
            if [[ ! $cw ]];then
                continue;
            fi
            let cur_idx=$(cut <<<"$cw" -d: -f1)
            cur_str=$(cut <<<"$cw" -d: -f2-)
            let cur_len=${#cur_str}
            pre_str=${line:$pre_end:$(($cur_idx-$pre_end))}
            replace_str=$(echo -n "$cur_str"|sed 's/_/ /g'|sed 's/\b./\u&/g'|sed 's/ //g'|sed 's/^./\l&/g')
            sb="$sb$pre_str$replace_str"
            let pre_end=$(($cur_idx + $cur_len))
        done <<< $(grep <<<"$line" -b -oP "$pat")
        sb="$sb${line:$pre_end}"$'\n'
    done
    echo -n "$sb"
}

