#!/usr/bin/awk -f
{
	typ=$2;
	rep="0";
	if(match(typ, /([a-zA-Z0-9]+)(\[\])/ ,m)){
		rep="1";
		typ=m[1]
	};
	if(typ=="string"){
		typ="String"
	}
	if(typ=="int32"){
		typ="Integer"
	}
	if(typ=="int64"){
		typ="Long"
	}
	if(rep=="1"){
		typ="List<" typ ">"
	}
	print "\t/**" $4 "*/\n\tprivate " typ " " $1 ";"
}
