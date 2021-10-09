#!/usr/bin/awk

# usage: echo "my name is user_id"|awk -f replace.awk -v P='\\w+(_\\w+)+' -v R=aa  
# usage: echo "my name is user_id"|awk -f replace.awk -v P='\\w+(_\\w+)+' -v CMD="sed 's/_/ /g'|sed 's/\\\\b./\\\\u&/g'|sed 's/ //g'|sed 's/^./\\\\l&/g'"

{
        s = $0;
        retstr = "";
        while(match(s,P,m)){
                start = m[0,"start"]
                len = m[0,"length"]
                if(CMD){
                        comm = "echo \"" m[0] "\"|" CMD
                        comm | getline r
                        close(comm)
                }else{
                        r = R
                }
                retstr = retstr substr(s,0,start-1) r
                s = substr(s,start+len)
        }
        retstr = retstr s
        print retstr
}
