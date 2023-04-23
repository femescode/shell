#!/usr/bin/env bash

jvm_dumping() {
  ls -l /proc/"$1"/fd | grep '\.hprof$'
}

pid=$(ps h -o pid --sort=-pmem -C java | head -n1 | xargs)
if [[ ! "$pid" ]]; then
  echo "Not found java process!"
elif [[ $(jstat -gcutil "$pid" | awk 'NR>1 && $4>80{print $4}') ]]; then
  echo "High heap occupancy, perform dumping and cleanups..."
  # print current user
  id
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
  (jstack "$pid" || jstack -F "$pid") >/home/work/logs/applogs/jstack.log
  if [[ $jmap_opt -eq 1 && ! -f /home/work/logs/applogs/heap.hprof ]]; then
    jmap -dump:format=b,file=/home/work/logs/applogs/heap.hprof "$pid"
    if [[ $? -ne 0 ]]; then
      # trigger linux kernel to coredump, then you can use jmap convert coredump to hprof
      mkdir -p /home/work/logs/applogs && ln -s /home/work/logs/applogs /home/core
      kill -6 "$pid"
    fi
  fi
elif [[ "$1" ]] && ! curl --connect-timeout 1 -m 1 -sS "$1"; then
  echo "Health check failed, perform dumping and cleanups..."
  (jstack "$pid" || jstack -F "$pid") >/home/work/logs/applogs/jstack.log
  ps h -L -o s,wchan -p "$pid"|sort|uniq -c >/home/work/logs/applogs/thread_state.log
else
  echo "Normal heap occupancy. Exiting gracefully."
fi
