#!/bin/bash

ngrep -d any -W single -s 200 -T 'select|def'|awk '{print} $1~/T/ && $2>0.2 && $2<1000 && /.def./{exit(0)}'
