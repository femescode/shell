#!/bin/bash

active_thread_kstack(){
  # 打印当前系统活跃java线程的内核栈
  ps h -Lo pid,tid,s,pcpu,comm,wchan:32 -C java|grep '[RD] '| awk '
    BEGIN{
        syscall_files["/usr/include/asm/unistd_64.h"]=1;
        syscall_files["/usr/include/x86_64-linux-gnu/asm/unistd_64.h"]=1;
        syscall_files["/usr/include/asm-x86_64/unistd.h"]=1;
        for(tfile in syscall_files){
            cmd="ls "tfile
            if(system(cmd)==0){
                hfile=tfile;
                break;
            }
        }
        if(!hfile){
            print "not found syscall header file!";
            exit 1;
        }
        while (getline <hfile){
            if($0 ~ /__NR_/){
                syscall_map[$3]=gensub(/__NR_/,"","g",$2)
            }
        }
        syscall_with_fd_map["read"]=1;
        syscall_with_fd_map["write"]=1;
        syscall_with_fd_map["pread64"]=1;
        syscall_with_fd_map["pwrite64"]=1;
        syscall_with_fd_map["fsync"]=1;
        syscall_with_fd_map["fdatasync"]=1;
        syscall_with_fd_map["recvfrom"]=1;
        syscall_with_fd_map["sendto"]=1;
        syscall_with_fd_map["recvmsg"]=1;
        syscall_with_fd_map["sendmsg"]=1;
        syscall_with_fd_map["epoll_wait"]=1;
        syscall_with_fd_map["ioctl"]=1;
        syscall_with_fd_map["accept"]=1;
        syscall_with_fd_map["accept4"]=1;
        special_fd_map["0"]="(stdin)";
        special_fd_map["1"]="(stdout)";
        special_fd_map["2"]="(stderr)";
    }
    {
        RS="^$";
        getline wchan <("/proc/"$1"/task/"$2"/wchan");
        close("/proc/"$1"/task/"$2"/wchan");
        getline stack <("/proc/"$1"/task/"$2"/stack");
        close("/proc/"$1"/task/"$2"/stack");
        getline syscall <("/proc/"$1"/task/"$2"/syscall");
        close("/proc/"$1"/task/"$2"/syscall");
        split(syscall, syscall_arr, /\s+/);
        syscall_id=syscall_arr[1]
        syscall_name=syscall_map[syscall_id];
        if(syscall_name in syscall_with_fd_map){
            fd=strtonum(syscall_arr[2])
            cmd="readlink /proc/"$1"/fd/"fd;
            cmd|getline filename;
            close(cmd);
            if(fd in special_fd_map){
                filename=filename special_fd_map[syscall_id]
            }
        }
        printf "pid:%s,tid:%s,stat:%s,pcpu:%s,comm:%s,wchan:%s,syscall:%s,filename:%s\n",$1,$2,$3,$4,$5,wchan,syscall_name,filename;
        print stack;
        RS="\n"
    }'
}

echo "active_thread_kstack: $(active_thread_kstack|sed -z 's/\n/   /g'), dmesg_100: $(dmesg -T|tail -n100|sed -z 's/\n/   /g')"
