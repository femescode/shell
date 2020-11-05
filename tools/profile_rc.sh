#!/usr/bin/env bash

git-branch-name() {
  git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3-
}
git-branch-prompt() {
  local branch=`git-branch-name`
  if [ $branch ]; then printf " [%s]" $branch; fi
}
is_git_bash() {
    cur_uname=$(uname -a)
    if [[ $cur_uname =~ 'MINGW' ]]; then
        return 0
    fi
    return 1
}
if ! is_git_bash; then
    PS1="\[\e[01;32m\]\u@\h \[\e[33m\]\w\[\e[0m\] \[\033[0;36m\]$(git-branch-prompt)\[\033[0m\] \n\$ "
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


odcat(){
    if [[ $1 ]];then
        cat $1|od -An -t a|tr -d "\n"|sed 's/nl/nl\n/g'
    else
        cat|od -An -t a|tr -d "\n"|sed 's/nl/nl\n/g'
    fi
}


ogrep ()
{
    p=$(printf '%s\n' "$@"|paste -s -d'|')
    grep -onP "$p"|awk '{i=index($0,":");a=substr($0,0,i-1);b=substr($0,i+1);r[a]=r[a] b "\t";} END{for(j in r){print r[j]}}'
}

xread(){
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

mysql2csv(){
    grep -P '^(\+\-|\|\s)' |sed '/^\+\-/d'|sed -E 's/^\s*\|[ \t]*//g'|sed -E 's/\s*\|[ \t]*$//g'|sed -E 's/[ \t]*\|[ \t]*/,/g'
}

x5decode(){
    base64 -d|jq '.body|fromjson'
}

