#!/usr/bin/env python
# coding:utf-8

import collections
import io
import re,datetime,time,json,sys,argparse,subprocess,os
import tempfile

DEV_NULL = os.open(os.devnull, os.O_RDWR)

def exists_cmd(cmd):
    return subprocess.call(["which", cmd],stdout=DEV_NULL) == 0

def run_cmd(cmd_args, shell=False):
    proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    stdout, stderr = proc.communicate()
    stdout = stdout.decode('UTF-8')
    stderr = stderr.decode('UTF-8')
    if stderr:
        sys.stderr.write(stderr)
        sys.exit(1)
    return stdout.strip()

def cost_show(cost):
    if cost > 1:
        return "%.3fs" % (cost)
    if cost * 1000 > 1:
        return "%.3fms" % (cost * 1000)
    if cost * 1000000 > 1:
        return "%.0fus" % (cost * 1000000)
    return str(cost) + 's'

def is_request(args, payload, src_ip, src_port, dst_ip, dst_port):
    if args.in_request and dst_ip not in args.local_ip:
        return False
    if args.out_request and src_ip not in args.local_ip:
        return False
    if args.request_regex:
        if not (src_port >= args.min_local_port and dst_port < args.min_local_port):
            return False
        if re.search(args.request_regex, payload, re.I):
            return True
    else:
        if (src_port >= args.min_local_port and dst_port < args.min_local_port):
            return True
        if re.search(r'^(POST|GET) /[^ ]* HTTP/1.[01]', payload):
            return True
        if re.search(r'\.\.\.(select[\.\s].+[\.\s]from[\.\s]|insert[\.\s]+into[\.\s]|update[\.\s].+[\.\s]set[\.\s]|delete[\.\s]+from[\.\s]|replace[\.\s]+into[\.\s])', payload, re.I):
            return True
    return False

class NetPacket:
    def __init__(self, timestr, timestamp, src_ip, src_port, dst_ip, dst_port, tcp_flag, payloads):
        self.timestr = timestr
        self.timestamp = timestamp
        self.src_ip = src_ip
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.tcp_flag = tcp_flag
        self.payloads = payloads
    def append(self, payload):
        self.payloads.append(payload)

def trace_ngrep_slow(args, cmd, inputStream):
    pre_packet_map = {}
    netPacket = None
    for line in iter(inputStream.readline, b''):
        if not line:
            continue
        line=line.strip()
        if cmd == 'ngrep':
            if not line.startswith('T '):
                continue
            columns = line.split(" ", 7)
            if len(columns) < 8:
                continue
            timestr = columns[1] + " " + columns[2]
            dt = datetime.datetime.strptime(timestr,"%Y/%m/%d %H:%M:%S.%f")
            timestamp = time.mktime(dt.timetuple()) + (dt.microsecond/1000000.0)
            src_addr = columns[3]
            dst_addr = columns[5]
            tcp_flag = columns[6]
            payload = columns[7]
            (src_ip, src_port) = src_addr.split(":")
            (dst_ip, dst_port) = dst_addr.split(":")
            record_packet(args, pre_packet_map, NetPacket(timestr, timestamp, src_ip, src_port, dst_ip, dst_port, tcp_flag, [payload]))
        elif cmd == 'tcpdump':
            m = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}) \w+ (\S+)\.(\d+) > (\S+)\.(\d+): Flags (\S+),.*$', line, re.I)
            if not m:
                if netPacket:
                    netPacket.append(line)
                continue
            if netPacket:
                record_packet(args, pre_packet_map, netPacket)
            timestr = m.group(1)
            dt = datetime.datetime.strptime(timestr,"%Y-%m-%d %H:%M:%S.%f")
            timestamp = time.mktime(dt.timetuple()) + (dt.microsecond/1000000.0)
            src_ip = m.group(2)
            src_port = m.group(3)
            dst_ip = m.group(4)
            dst_port = m.group(5)
            tcp_flag = m.group(6)
            netPacket = NetPacket(timestr, timestamp, src_ip, src_port, dst_ip, dst_port, tcp_flag, [])

def record_packet(args, pre_packet_map, netPacket):
    timestr = netPacket.timestr
    timestamp = netPacket.timestamp
    src_ip = netPacket.src_ip
    src_port = netPacket.src_port
    dst_ip = netPacket.dst_ip
    dst_port = netPacket.dst_port
    tcp_flag = netPacket.tcp_flag
    payload = " \n ".join(netPacket.payloads)
    
    src_addr = "%s:%s" % (src_ip, src_port)
    dst_addr = "%s:%s" % (dst_ip, dst_port)
    packet_prefix = "%s %s %s %s %s" % (timestr, src_addr, '->', dst_addr, tcp_flag)
    req_addr_pair = src_addr + "-" + dst_addr
    resp_addr_pair = dst_addr + "-" + src_addr

    pre_packet = None
    if req_addr_pair in pre_packet_map:
        pre_packet = pre_packet_map.get(req_addr_pair)
    if resp_addr_pair in pre_packet_map:
        pre_packet = pre_packet_map.get(resp_addr_pair)
    if is_request(args, payload, src_ip, int(src_port), dst_ip, int(dst_port)):
        if tcp_flag in ['[A]','[.]']:
            return
        # 发包，记录时间缀
        packet = collections.OrderedDict({})
        packet['start'] = timestamp
        packet['req'] = payload
        packet['resp'] = ''
        packet['packets'] = [packet_prefix]
        packet['cost'] = ''
        pre_packet_map[src_addr+"-"+dst_addr] = packet
    elif pre_packet:
        pre_packet['packets'].append(packet_prefix)
        if resp_addr_pair in pre_packet_map:
            # 收包，计算时间差
            pre_timestamp = pre_packet.get('start')
            cost = timestamp - pre_timestamp
            if tcp_flag in ['[A]','[.]']:
                pre_packet['ack_rtt'] = cost_show(cost)
                return
            pre_packet['cost'] = cost_show(cost)
            pre_packet['resp'] = payload
            if cost * 1000 > args.timeout:
                print(json.dumps(pre_packet, indent=2))
            del pre_packet_map[resp_addr_pair]

def get_ngrep_cmd_args(args):
    if args.input_file:
        cmd_args = ["ngrep","-I", args.input_file,"-S","800"]
    else:
        cmd_args = ["ngrep","-d","any","-s","800"]
    cmd_args.extend(["-W","single","-t","-l"])
    if args.output_file:
        cmd_args.extend(["-O", args.output_file])
    cmd_args.append("")
    if args.bpf_filter != "":
        cmd_args.append(args.bpf_filter)
    return cmd_args

def get_tcpdump_cmd_args(args):
    if args.input_file:
        cmd_args = ["tcpdump","-r", args.input_file]
    else:
        cmd_args = ["tcpdump", "-i", "any","-s","800"]
    cmd_args.extend(["-nnn", "-A", "-tttt","-l"])
    if args.output_file:
        cmd_args.extend(["-w", args.output_file])
    if args.bpf_filter != "":
        cmd_args.append(args.bpf_filter)
    return cmd_args

def main():
    parser = argparse.ArgumentParser(description='ngrep traffic slow response trace tools.',
            usage="python -u ngrep_slow.py 'port 80' -o -t 1000")
    parser.add_argument('bpf_filter', default="", help="bpf filter, eg: port 8080")
    parser.add_argument("-t", "--timeout", type=int, default=0, help='the timeout millisecond.')
    parser.add_argument("-i", "--in_request", action="store_true", help='trace in request packet.')
    parser.add_argument("-o", "--out_request", action="store_true", help='trace out request packet.')
    parser.add_argument('-r', '--request_regex', default=None, required=False)
    parser.add_argument("--min_local_port", type=int, default=32768, help='set tcp client min local port range')
    parser.add_argument("-I", "--input_file", default=None, required=False, help='read packet stream from pcap format file pcap_dump.')
    parser.add_argument("-O", "--output_file", default=None, required=False, help='dump matched packets in pcap format to pcap_dump')
    parser.add_argument("--local_ip", type=str, help='local ip list')
    parser.add_argument("--ngrep", action="store_true", help='use ngrep')
    parser.add_argument("--tcpdump", action="store_true", help='use tcpdump')
    args = parser.parse_args()

    if not args.local_ip:
        args.local_ip = run_cmd("ifconfig|awk -v RS= '!/lo/{print $6}'", shell=True).split()
    else:
        args.local_ip = args.local_ip.split()
    
    if args.tcpdump:
        cmd = "tcpdump"
        cmd_args=get_tcpdump_cmd_args(args)
    elif args.ngrep:
        cmd = "ngrep"
        cmd_args=get_ngrep_cmd_args(args)
    elif exists_cmd("tcpdump"):
        cmd = "tcpdump"
        cmd_args=get_tcpdump_cmd_args(args)
    elif exists_cmd("ngrep"):
        cmd = "ngrep"
        cmd_args=get_ngrep_cmd_args(args)
    else:
        sys.stderr.write("tcpdump or ngrep not found! \n")
        sys.exit(1)
    
    sys.stderr.write("capture traffic with '%s'\n" % (" ".join(cmd_args)))
    proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
    try:
        trace_ngrep_slow(args, cmd, proc.stdout)
    except (KeyboardInterrupt) as e:
        pass
    finally:
        proc.stdout.close()
        sys.stderr.write(proc.stderr.read()+"\n")
        proc.stderr.close()
        proc.kill()

main()