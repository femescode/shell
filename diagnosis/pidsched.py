#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import argparse
import io
import time
from datetime import datetime
import json
import re
import subprocess

class Process:
    def __init__(self, pid):
        self._pid = int(pid)
        self.read_proc()
        self._cur_schedstat_map = None

    def read_proc(self):
        proc_map = {}
        with io.open("/proc/%d/status" % (self._pid), "r", encoding='utf-8') as f:
            for line in f:
                (key, value) = re.split(r'\s*:\s*', line)
                proc_map[key] = value
        self._proc_map = proc_map

    def is_process(self):
        return self._proc_map.get("Pid") == self._proc_map.get("Tgid")

    def read_schedstat_file(self, filePath):
        with io.open(filePath, "r", encoding='utf-8') as f:
            arr = f.read().split()
            return [int(arr[0]), int(arr[1]), int(arr[2])]

    def read_schedstat(self):
        # 保存之前的schedstat数据
        if self._cur_schedstat_map is None:
            self._cur_schedstat_map = {}
        else:
            self._old_schedstat_map = self._cur_schedstat_map
            self._old_time = self._cur_time
            self._cur_schedstat_map = {}
        # 读取最近的schedstat数据
        if self.is_process():
            self._tids = os.listdir("/proc/" + str(self._pid) + "/task/")
        else:
            self._tids = [self._pid]
        for tid in self._tids:
            try:
                (runing_ns, waitrun_ns, timeslice_num) = self.read_schedstat_file("/proc/" + str(self._pid) + "/task/" + str(tid) + "/schedstat")
            except IOError as e:
                continue
            self._cur_schedstat_map[tid]=[runing_ns, waitrun_ns, timeslice_num]
        # 更新时间
        self._cur_time = time.time() * 1000

    def calc_schedstat_delta(self):
        total_schedstat_delta = [0, 0, 0]
        max_oncpu_schedstat_delta = [0, 0, 0, 0]
        max_sched_delay_schedstat_delta = [0, 0, 0, 0]
        for tid in self._cur_schedstat_map.keys():
            cur_schedstat_arr = self._cur_schedstat_map.get(tid)
            old_schedstat_arr = self._old_schedstat_map.get(tid)
            if old_schedstat_arr is None:
                continue
            schedstat_delta = [(cur_schedstat_arr[0] - old_schedstat_arr[0]), (cur_schedstat_arr[1] - old_schedstat_arr[1]), (cur_schedstat_arr[2] - old_schedstat_arr[2]), tid]
            total_schedstat_delta = [(total_schedstat_delta[0]+schedstat_delta[0]), (total_schedstat_delta[1]+schedstat_delta[1]), (total_schedstat_delta[2]+schedstat_delta[2])]
            if schedstat_delta[0] > max_oncpu_schedstat_delta[0]:
                max_oncpu_schedstat_delta = schedstat_delta
            if schedstat_delta[1] > max_sched_delay_schedstat_delta[1]:
                max_sched_delay_schedstat_delta = schedstat_delta
        self._total_schedstat_delta = total_schedstat_delta
        self._max_oncpu_schedstat_delta = max_oncpu_schedstat_delta
        self._max_sched_delay_schedstat_delta = max_sched_delay_schedstat_delta

    def format_ms(self, ms):
        return "%-10s" % ("%.3fms" % (ms))

    def print_out(self):
        if self._old_time is None:
            return
        total_oncpu_ms = self._total_schedstat_delta[0]/1000000
        total_sched_delay_ms = self._total_schedstat_delta[1]/1000000
        total_ms = self._cur_time - self._old_time
        sleep_ms = total_ms - total_oncpu_ms - total_sched_delay_ms
        curtime = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%dT%H:%M:%S")
        print("%-20s pid:%s total:%s idle:%s oncpu:( %s max:%s cs:%-4s tid:%-6s ) sched_delay:( %s max:%s cs:%-3s tid:%-6s )" % (
            curtime, str(self._pid), self.format_ms(total_ms), self.format_ms(max(sleep_ms, 0)), 
            self.format_ms(total_oncpu_ms), self.format_ms(self._max_oncpu_schedstat_delta[0]/1000000), str(self._max_oncpu_schedstat_delta[2]), str(self._max_oncpu_schedstat_delta[3]), 
            self.format_ms(total_sched_delay_ms), self.format_ms(self._max_sched_delay_schedstat_delta[1]/1000000), str(self._max_sched_delay_schedstat_delta[2]), str(self._max_sched_delay_schedstat_delta[3])))

def main():
    parser = argparse.ArgumentParser(description='Monitor process latency by /proc.')
    parser.add_argument('pids', nargs='+')
    args = parser.parse_args()
    process_map = {}
    for pid in args.pids:
        process = Process(pid)
        process_map[pid]=process
        process.read_schedstat()
    while True:
        time.sleep(1)
        for pid in args.pids:
            process = process_map.get(pid)
            process.read_schedstat()
            process.calc_schedstat_delta()
            process.print_out()

main()
