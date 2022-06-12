#!/bin/bash

cmd_exists() {
    if [ -x "$(command -v "$1")" ]; then
        return 0;
    else
       return 1;
    fi
}

url=https://gitee.com/fmer/shell/raw/master
if [[ $1 ]];then
    url=$1
fi

dir="$(mktemp -d)"
cd $dir

tmpcmd="curl -s $url/init_sh/my_bashrc.sh -o /etc/my_bashrc.sh"

if cmd_exists "sudo"; then
    sudo $tmpcmd
else
    $tmpcmd
fi

if [[ ! $(grep my_bashrc ~/.bashrc) ]]; then
    cat >> ~/.bashrc <<eof

if [ -f /etc/my_bashrc.sh ]; then
    source /etc/my_bashrc.sh
fi

eof

fi

curl -s $url/init_sh/my_vimrc -o ~/.vimrc 

rm -rf $dir

exit 0
