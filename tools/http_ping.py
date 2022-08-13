#!/usr/bin/env python
# encoding: utf-8

import sys,requests,time,json,hashlib,base64,uuid,io,os,argparse,re
s = requests.Session()
s.mount('https://', requests.adapters.HTTPAdapter(pool_connections=200, pool_maxsize=200))
s.mount('http://', requests.adapters.HTTPAdapter(pool_connections=200, pool_maxsize=200))

def http_ping(seq, args):
    logid = uuid.uuid1().hex
    url = args.url
    headers = {}
    headers['User-Agent']='curl_' + str(logid)
    if args.header:
        for header in args.header:
            (key, value) = re.split(r'\s*:\s*', header.strip())
            headers[key] = value
    start = time.time()
    if args.request == "GET":
        resp = s.get(url,headers=headers, timeout=6000)
    else:
        resp = s.post(url,data=args.data,headers=headers, timeout=6000)
    end = time.time()
    ret = resp.content.decode("UTF-8").replace("\r","").replace("\n","")
    print("time=%s seq=%d logid=%s cost=%.3fms" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start)), seq, logid, (end - start) * 1000))


parser = argparse.ArgumentParser(description='http ping test tools.')
parser.add_argument('url')
parser.add_argument('-X', "--request", type=str, choices=["GET", "POST"], default="GET", help='request method.')
parser.add_argument('-d', "--data", type=str, help='request data.')
parser.add_argument('-H', "--header", type=str, nargs='*', help='request header.')
args = parser.parse_args()

i = 0
while True:
    http_ping(i, args)
    time.sleep(1)
    i = i + 1
