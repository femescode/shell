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
has_rpm(){
    [[ $(rpm -qa|grep "$1") ]] && return 0 || return 1
}

url=https://gitee.com/fmer/shell/raw/master
if [[ $1 ]];then
    url=$1
fi

dir="$HOME/.command_init"
if [[ ! -e "$dir" ]]; then
    mkdir -p "$dir"
fi
cd "$dir"


#安装命令
install_redhat(){
    if curl -s -o /dev/null www.baidu.com; then
        yum install -y curl vim jq pv cv openssh-clients lsof bc psmisc iproute tcpdump ngrep nmap-ncat socat
    else
        install_redhat_local
    fi
}
install_redhat_local(){
    if ! cmd_exists "nc"; then
        if ! has_rpm "libpcap"; then
            execute "curl -s -LO $url/yum/nc/libpcap-1.5.3-8.el7.x86_64.rpm" "下载libpcap-1.5.3-8.el7.x86_64.rpm"
            execute "rpm -i libpcap-1.5.3-8.el7.x86_64.rpm" "安装libpcap-1.5.3-8.el7.x86_64.rpm"
        fi
        if ! has_rpm "nmap-ncat"; then
            execute "curl -s -LO $url/yum/nc/nmap-ncat-6.40-7.el7.x86_64.rpm" "下载nmap-ncat-6.40-7.el7.x86_64.rpm"
            execute "rpm -i nmap-ncat-6.40-7.el7.x86_64.rpm" "安装nmap-ncat-6.40-7.el7.x86_64.rpm"
        fi
    fi

    if ! cmd_exists "pv"; then
        execute "curl -s -LO $url/yum/pv/pv-1.4.6-1.el7.x86_64.rpm" "下载pv-1.4.6-1.el7.x86_64.rpm"
        execute "rpm --nosignature -i pv-1.4.6-1.el7.x86_64.rpm" "安装pv-1.4.6-1.el7.x86_64.rpm"
    fi

    if ! cmd_exists "lsof"; then
        execute "curl -s -LO $url/yum/lsof/lsof-4.87-6.el7.x86_64.rpm" "下载lsof-4.87-6.el7.x86_64.rpm"
        execute "rpm -i lsof-4.87-6.el7.x86_64.rpm" "安装lsof-4.87-6.el7.x86_64.rpm"
    fi

    if ! cmd_exists "ss"; then
        if ! has_rpm "libmnl"; then
            execute "curl -s -LO $url/yum/ss/libmnl-1.0.3-7.el7.x86_64.rpm" "下载libmnl-1.0.3-7.el7.x86_64.rpm"
            execute "rpm -i libmnl-1.0.3-7.el7.x86_64.rpm" "安装libmnl-1.0.3-7.el7.x86_64.rpm"
        fi
        if ! has_rpm "libnfnetlink"; then
            execute "curl -s -LO $url/yum/ss/libnfnetlink-1.0.1-4.el7.x86_64.rpm" "下载libnfnetlink-1.0.1-4.el7.x86_64.rpm"
            execute "rpm -i libnfnetlink-1.0.1-4.el7.x86_64.rpm" "安装libnfnetlink-1.0.1-4.el7.x86_64.rpm"
        fi
        if ! has_rpm "libnetfilter_conntrack"; then
            execute "curl -s -LO $url/yum/ss/libnetfilter_conntrack-1.0.4-2.el7.x86_64.rpm" "下载libnetfilter_conntrack-1.0.4-2.el7.x86_64.rpm"
            execute "rpm -i libnetfilter_conntrack-1.0.4-2.el7.x86_64.rpm" "安装libnetfilter_conntrack-1.0.4-2.el7.x86_64.rpm"
        fi
        if ! has_rpm "iptables"; then
            execute "curl -s -LO $url/yum/ss/iptables-1.4.21-17.el7.x86_64.rpm" "下载iptables-1.4.21-17.el7.x86_64.rpm"
            execute "rpm -i iptables-1.4.21-17.el7.x86_64.rpm" "安装iptables-1.4.21-17.el7.x86_64.rpm"
        fi
        if ! has_rpm "iproute"; then
            execute "curl -s -LO $url/yum/ss/iproute-3.10.0-74.el7.x86_64.rpm" "下载iproute-3.10.0-74.el7.x86_64.rpm"
            execute "rpm -i iproute-3.10.0-74.el7.x86_64.rpm" "安装iproute-3.10.0-74.el7.x86_64.rpm"
        fi
    fi

    if ! cmd_exists "socat"; then
        execute "curl -s -LO $url/yum/socat/socat-1.7.2.2-5.el7.x86_64.rpm" "下载socat-1.7.2.2-5.el7.x86_64.rpm"
        execute "rpm -i socat-1.7.2.2-5.el7.x86_64.rpm" "安装socat-1.7.2.2-5.el7.x86_64.rpm"
    fi
}
install_ubuntu(){
    sudo apt install -y curl vim jq pv progress openssh-client lsof bc psmisc iproute2 tcpdump ngrep ncat socat moreutils dateutils python3-q-text-as-data parallel tmux sysstat iotop iftop dstat nmon
}
if [[ -f /etc/redhat-release ]];then
    install_redhat
else
    install_ubuntu
fi

print_success "成功！"

exit 0
