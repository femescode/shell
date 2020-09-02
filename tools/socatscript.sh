#!/bin/bash

SOCKDIR=$(mktemp -d)
SOCKF=${SOCKDIR}/usock
SESSION_NAME=${1:-socatSession}
WINDOW_NAME=${2:-socatWindown}

# create session and window
tmux has-session -t $SESSION_NAME
if [[ $? -eq 1 ]];then
    tmux new -s $SESSION_NAME -n $WINDOW_NAME -d "socat file:\`tty\`,raw,echo=0 exec:'ncat -lk 9998'"
fi
# split windown 0
tmux split-window -h -t 0 "socat file:\`tty\`,raw,echo=0 UNIX-LISTEN:${SOCKF},umask=0077"
tmux select-pane -t 0
tmux select-layout -t $WINDOW_NAME main-horizontal
tmux resize-pane -t 0 -y 1
# Wait for socket
while test ! -e ${SOCKF} ; do sleep 1 ; done
# Use socat to ship data between the unix socket and STDIO.
socat -U STDOUT TCP:localhost:9998 &
exec socat STDIO UNIX-CONNECT:${SOCKF}
