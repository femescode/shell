#! /bin/bash

cmd_exists() {
    if [ -x "$(command -v "$1")" ]; then
        return 0;
    else
       return 1;
    fi
}
getsudo() {
    if cmd_exists "sudo"; then
        echo -n sudo
    else
        echo -n ""
    fi
}

print_success() {
    # Print output in green
    printf "\e[0;32m  [✔] $1\e[0m\n"
}
print_error() {
    # Print output in red
    printf "\e[0;31m  [✖] $1 $2\e[0m\n"
}

print_error_exit() {
    print_error "$@"
    exit 1
}
execute() {
    $1 
    if [[ $? -eq 0 ]];then
        print_success "${2:-$1}"
    else
	    print_error_exit "${2:-$1}"
	fi
}

url=https://gitee.com/fmer/shell/raw/master
if [[ $1 ]];then
    url=$1
fi

if [[ ! -e "/tmp/command_init" ]]; then
    mkdir -p "/tmp/command_init"
fi
cd /tmp/command_init

#自定义命令
if ! cmd_exists "jthreadtop"; then
    execute "curl -s -LO $url/tools/jthreadtop.sh" "下载jthreadtop.sh"
    $(getsudo) ln -s -T /tmp/command_init/jthreadtop.sh /usr/bin/jthreadtop
    $(getsudo) chmod +x /usr/bin/jthreadtop
fi
if ! cmd_exists "humantime"; then
    execute "curl -s -LO $url/tools/humantime.py" "下载humantime.py"
    $(getsudo) ln -s -T /tmp/command_init/humantime.py /usr/bin/humantime
    $(getsudo) chmod +x /usr/bin/humantime
fi
if ! cmd_exists "json2csv"; then
    execute "curl -s -LO $url/tools/json2csv.py" "下载json2csv.py"
    $(getsudo) ln -s -T /tmp/command_init/json2csv.py /usr/bin/json2csv
    $(getsudo) chmod +x /usr/bin/json2csv
fi
if ! cmd_exists "socatscript"; then
    execute "curl -s -LO $url/tools/socatscript.sh" "下载socatscript.sh"
    $(getsudo) ln -s -T /tmp/command_init/socatscript.sh /usr/bin/socatscript
    $(getsudo) chmod +x /usr/bin/socatscript
fi
if ! cmd_exists "list2proto"; then
    execute "curl -s -LO $url/tools/list2proto.awk" "下载list2proto.awk"
    $(getsudo) ln -s -T /tmp/command_init/list2proto.awk /usr/bin/list2proto
    $(getsudo) chmod +x /usr/bin/list2proto
fi
if ! cmd_exists "list2bean"; then
    execute "curl -s -LO $url/tools/list2bean.awk" "下载list2bean.awk"
    $(getsudo) ln -s -T /tmp/command_init/list2bean.awk /usr/bin/list2bean
    $(getsudo) chmod +x /usr/bin/list2bean
fi

#安装命令
install_redhat(){
    if ! cmd_exists "nc"; then
        execute "curl -s -LO $url/yum/nc/libpcap-1.5.3-8.el7.x86_64.rpm" "下载libpcap-1.5.3-8.el7.x86_64.rpm"
        execute "rpm -i libpcap-1.5.3-8.el7.x86_64.rpm" "安装libpcap-1.5.3-8.el7.x86_64.rpm"
        execute "curl -s -LO $url/yum/nc/nmap-ncat-6.40-7.el7.x86_64.rpm" "下载nmap-ncat-6.40-7.el7.x86_64.rpm"
        execute "rpm -i nmap-ncat-6.40-7.el7.x86_64.rpm" "安装nmap-ncat-6.40-7.el7.x86_64.rpm"
    fi

    if ! cmd_exists "pv"; then
        execute "curl -s -LO $url/yum/pv/pv-1.4.6-1.el7.x86_64.rpm" "下载pv-1.4.6-1.el7.x86_64.rpm"
        execute "rpm -i pv-1.4.6-1.el7.x86_64.rpm" "安装pv-1.4.6-1.el7.x86_64.rpm"
    fi

    if ! cmd_exists "lsof"; then
        execute "curl -s -LO $url/yum/lsof/lsof-4.87-6.el7.x86_64.rpm" "下载lsof-4.87-6.el7.x86_64.rpm"
        execute "rpm -i lsof-4.87-6.el7.x86_64.rpm" "安装lsof-4.87-6.el7.x86_64.rpm"
    fi

    if ! cmd_exists "ss"; then
        execute "curl -s -LO $url/yum/ss/libmnl-1.0.3-7.el7.x86_64.rpm" "下载libmnl-1.0.3-7.el7.x86_64.rpm"
        execute "rpm -i libmnl-1.0.3-7.el7.x86_64.rpm" "安装libmnl-1.0.3-7.el7.x86_64.rpm"
        execute "curl -s -LO $url/yum/ss/libnfnetlink-1.0.1-4.el7.x86_64.rpm" "下载libnfnetlink-1.0.1-4.el7.x86_64.rpm"
        execute "rpm -i libnfnetlink-1.0.1-4.el7.x86_64.rpm" "安装libnfnetlink-1.0.1-4.el7.x86_64.rpm"
        execute "curl -s -LO $url/yum/ss/libnetfilter_conntrack-1.0.4-2.el7.x86_64.rpm" "下载libnetfilter_conntrack-1.0.4-2.el7.x86_64.rpm"
        execute "rpm -i libnetfilter_conntrack-1.0.4-2.el7.x86_64.rpm" "安装libnetfilter_conntrack-1.0.4-2.el7.x86_64.rpm"
        execute "curl -s -LO $url/yum/ss/iptables-1.4.21-17.el7.x86_64.rpm" "下载iptables-1.4.21-17.el7.x86_64.rpm"
        execute "rpm -i iptables-1.4.21-17.el7.x86_64.rpm" "安装iptables-1.4.21-17.el7.x86_64.rpm"
        execute "curl -s -LO $url/yum/ss/iproute-3.10.0-74.el7.x86_64.rpm" "下载iproute-3.10.0-74.el7.x86_64.rpm"
        execute "rpm -i iproute-3.10.0-74.el7.x86_64.rpm" "安装iproute-3.10.0-74.el7.x86_64.rpm"
    fi

    if ! cmd_exists "socat"; then
        execute "curl -s -LO $url/yum/socat/socat-1.7.2.2-5.el7.x86_64.rpm" "下载socat-1.7.2.2-5.el7.x86_64.rpm"
        execute "rpm -i socat-1.7.2.2-5.el7.x86_64.rpm" "安装socat-1.7.2.2-5.el7.x86_64.rpm"
    fi
}
install_ubuntu(){
    sudo apt install openssh-client lsof nmap psmisc iproute2 pv jq
}
if [[ -f /etc/redhat-release ]];then
    install_redhat
else
    install_ubuntu

print_success "成功！"

exit 0
