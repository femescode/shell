#!/usr/bin/env bash

git-branch-name() {
    git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3-
}
git-branch-prompt() {
    local branch=`git-branch-name`
    if [ $branch ]; then printf " [%s]" $branch; fi
}
curr_ip() {
    ifconfig|awk -v RS= '/eth0|ens33|wlan0/ || $6~/^(192|10)\./{print $6}'
}
is_git_bash() {
    cur_uname=$(uname -a)
    if [[ $cur_uname =~ 'MINGW' ]]; then
        return 0
    fi
    return 1
}
if ! is_git_bash; then
    PS1="\n\[\e[01;32m\]\u@\$(curr_ip):\[\e[33m\]\$PWD\[\e[0m\] \[\033[0;36m\]\$(git-branch-prompt)\[\033[0m\] \n\$ "
fi

#修改ll时间格式
export TIME_STYLE='+%Y-%m-%d %H:%M:%S'
alias ll='ls -lh'
alias urlencode='python -c "import sys, urllib as ul; print ul.quote_plus(sys.argv[1])"'
alias urldecode='python -c "import sys, urllib as ul; print ul.unquote_plus(sys.argv[1])"'

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


ogrep ()
{
    p=$(printf '%s\n' "$@"|paste -s -d'|')
    grep -onP "$p"|awk -F: '{if(!S[$1]++){if(NR>1){printf "\n"} printf "%s:%s",$1,$2}else {printf ",%s",$2}}'
}

xpipe(){
    while true ; do
        case "$1" in
                -n*|--max-args) 
                    if [[ "$1" == "-n" || "$1" == "--max-args" ]];then 
                        MAX_ARGS="-n $2";shift 2; 
                    else 
                        MAX_ARGS="$1";shift 1; 
                    fi ;;
                -P*|--max-procs) 
                    if [[ "$1" == "-P" || "$1" == "--max-procs" ]];then 
                        MAX_PROCS="-P $2";shift 2; 
                    else 
                        MAX_PROCS="$1";shift 1; 
                    fi ;;
                -L*|--max-lines) 
                    if [[ "$1" == "-L" || "$1" == "--max-lines" ]];then 
                        MAX_LINES="-L $2";shift 2; 
                    else 
                        MAX_LINES="$1";shift 1; 
                    fi ;;
                -p|--interactive) 
                    INTERACTIVE="$1";shift 1 ;;
                *) break ;;
        esac
    done
    xargs -d"\n" $MAX_ARGS $MAX_PROCS $MAX_LINES $INTERACTIVE bash -c "printf '%s\n' \"\$@\"|$*" ''
    return 0
}
