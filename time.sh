#!/bin/bash
echo "gmailfs start"
echo "time: cd into /inbox"
time cd ./client/inbox > perf.out
echo "time: [/inbox] ls"
time ls > /dev/null
cd ../
cd ../
echo "time: [in-cache] cd"
time cd ./client/inbox/'[in-cache] long & attachment ID 175a8e5b2271e579'
echo "time: [in-cache] ls"
time ls > /dev/null
echo "time: [in-cache] cat content.html"
time cat content.html  > /dev/null
echo "time: [in-cache] cat content.txt"
time cat content.txt > /dev/null
printf "\n"
printf "NOT IN CACHE"
printf "\n"
cd ../
for path in 'Long email test ID 17519a4cd78744f9' 'test from bletsch ID 17589c9906a2afff' 'Long email test ID 17519a4cd78744f9'
  do
    echo "time: [not-in-cache] cd $path"
    time cd "./$path"
    echo "time: [not-in-cache] ls $path"
    time ls > /dev/null
    echo "time: [not-in-cache] cat content.html"
    time cat content.html > /dev/null
    echo "time: [not-in-cache] cat content.txt"
    time cat content.txt > /dev/null
    cd ../
  done