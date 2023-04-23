#!/bin/bash

jvm_dumping() {
  ls -l /proc/"$1"/fd | grep '\.hprof$'
}

while sleep 1; do
  now_time=$(date +%F_%H-%M-%S)
  # get java pid
  pid=$(ps h -o pid --sort=-pmem -C java | head -n1 | xargs)
  [[ ! $pid ]] && {
    unset n pre_fgc
    sleep 1m
    continue
  }
  # get old space usage, fgc count
  data=$(jstat -gcutil "$pid" | awk 'NR>1{print $4,$(NF-2)}')
  read -r old fgc <<<"$data"
  echo "$now_time: $old $fgc"
  if [[ $(echo "$old" | awk '$1>80{print $0}') ]]; then
    ((n++))
  else
    ((n = 0))
  fi
  # over 80% for 3 consecutive times, or over 80% after fgc
  if [[ $n -ge 3 || $pre_fgc && $fgc -gt $pre_fgc && $n -ge 1 ]]; then
    jmap_opt=1
    # has another jmap, wait it completed and not jmap again
    if pgrep jmap; then
      while sleep 2s; do pgrep jmap || break; done
      jmap_opt=0
    fi
    # jvm dumping heap,  wait it completed and not jmap again
    if jvm_dumping "$pid"; then
      while sleep 2s; do jvm_dumping "$pid" || break; done
      jmap_opt=0
    fi
    # dump the jstack and jmap
    jstack "$pid" >/home/work/logs/applogs/jstack-"$now_time".log
    if [[ $jmap_opt -eq 1 ]]; then
      if [[ "$*" =~ dump ]]; then
        jmap -dump:format=b,file=/home/work/logs/applogs/heap-"$now_time".hprof "$pid"
      else
        jmap -histo "$pid" >/home/work/logs/applogs/histo-"$now_time".log
      fi
    fi
    {
      unset n pre_fgc
      # delete old dump file, avoid disk overflow
      ls -t /home/work/logs/applogs/jstack-* | tail -n+3 | xargs -r rm
      ls -t /home/work/logs/applogs/heap-* | tail -n+3 | xargs -r rm
      ls -t /home/work/logs/applogs/histo-* | tail -n+3 | xargs -r rm
      break
    }
  fi
  pre_fgc=$fgc
done
