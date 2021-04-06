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

dir="$(mktemp)"
cd $dir

tmpcmd="curl -s $url/tools/.profile_rc.sh -o /etc/.profile_rc.sh"

if cmd_exists "sudo"; then
    sudo $tmpcmd
else
    $tmpcmd
fi

if [[ ! $(grep profile_rc ~/.bashrc) ]]; then
    printf "\nif [ -f /etc/.profile_rc.sh ]; then\n\t. /etc/.profile_rc.sh\nfi" >> ~/.bashrc
fi

curl -s $url/tools/.vimrc -o ~/.vimrc 

rm -rf $dir

exit 0
