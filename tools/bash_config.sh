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

mkdir -p /tmp/shell-config
cd /tmp/shell-config
curl -s -LO $url/tools/profile_rc.sh
if [[ ! $(grep profile_rc ~/.bashrc) ]]; then
    printf "if [ -f /etc/.profile_rc.sh ]; then\n\t. /etc/.profile_rc.sh\nfi" >> ~/.bashrc
fi
if cmd_exists "sudo"; then
    sudo cp profile_rc.sh /etc/.profile_rc.sh
else
    cp profile_rc.sh /etc/.profile_rc.sh
fi

curl -s -LO $url/tools/vimrc
cp vimrc ~/.vimrc
rm -rf /tmp/shell-config
exit 0