#!/usr/bin/env python
# encoding: utf-8

import csv
import json
import sys
import codecs

def trans(content):
    items = json.loads(content)
    if not isinstance(items,list):
        raise Exception("不是json数组，无法处理！", items)
    # 这里添加quoting=csv.QUOTE_ALL的作用是将所有内容用引号包括起来，其
    # 作用是可以防止在用excel这类软件打开的时候，会自动判断内容里面的逗号
    # 就会将其识别为另外的列
    writer = csv.writer(sys.stdout, delimiter=',',quoting=csv.QUOTE_ALL)
    flag = True
    line_num =0
    for item in items:
        if flag:
            keys = list(item.keys())
            writer.writerow(keys)
            flag = False
        writer.writerow(list(item.values()))
        line_num+=1

if __name__ == '__main__':
    content = sys.stdin.read()
    trans(content)
