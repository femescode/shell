#!/bin/bash

tables=("$@")
HISTFILE=$(mktemp -p '' hist.XXXXXXXXXX)

show_tables(){
    grep -H . -m1 "${tables[@]}" | sed -E 's/\.(csv|tsv|txt)//g; s/:/\n/; i\\'
}
show_usage(){
    echo -e "Usage: "
    echo -e " 1) show tables"
    echo -e " 2) select * from xxx limit 10"
    echo -e " 3) exit"
}

show_usage
show_tables
while read -e -p $'\ncsv> ' line; do
    line="${line%%;}"
    if [[  -z "$line" ]]; then
        continue
    elif [[ "$line" == 'exit' ]]; then
        exit
    elif [[ "$line" == 'show tables' ]]; then
        show_tables
    elif [[ "$line" =~ ^select ]]; then
        csvsql --query "$line" "${tables[@]}" -y0 -I | csvformat -T -B -P '\' | column -s $'\t' -t | less -iNSFX
    else
        show_usage
    fi
    set -o histexpand
    set -o history
    history -s "$line"
done

rm "$HISTFILE"