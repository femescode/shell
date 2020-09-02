#!/usr/bin/awk
{
	typ=$2;
	rep="";
	if(match(typ, /([a-zA-Z0-9]+)(\[\])/ ,m)){
		rep="repeated ";
		typ=m[1]
	};
	if($3=="否" && rep==""){
		if(typ=="string"){
			typ="google.protobuf.StringValue"
		}
		if(typ=="int32"){
			typ="google.protobuf.Int32Value"
		}
		if(typ=="int64"){
			typ="google.protobuf.Int64Value"
		}
	}
	print "\t//" $4 "\n\t" rep typ " " $1 "=" NR ";"
}
