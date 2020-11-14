#!/bin/bash
echo "part1 perf test"
pwd=`pwd`
client_inbox="client/inbox"
src_inbox="src/inbox"
declare -a part1_emails=("Fwd: hey ID 175c7f18f6e97d62" "Fwd: Long email test ID 175c7f1524574467" "Fwd: test from bletsch ID 175c7f1c87e9740a")
#"hey ID 175a51ddd82e5c1a" 'Long email test ID 17519a4cd78744f9' "test from bletsch ID 17589c9906a2afff" "1MB ID 175c07cb69deb952"
declare -a part2_emails=("Fwd: 1MB ID 175c7dd949a689de" "Fwd: 5MB ID 175c7dfe72333042" "Fwd: 10MB ID 175c7e017a1ffcbc" "Fwd: 15MB ID 175c7e07830fcf36")
#for e in "${part1_emails[@]}";do
#  if [[ -d "$path/$e" ]]
#  then
#      echo "$e shouldn't be in cache folder now"
#      exit 1
#  fi
#done

TIMEFORMAT=%R
get_time="not_in_cache=$({ time ls -l >/dev/null; } 2>&1);in_cache=$({ time ls -l >/dev/null; } 2>&1);"

#echo "[PART 1]"

echo "part1","plain txt","wikipedia page","5M attachment" >> "$pwd/result.csv"
for i in {1..5}; do
  echo -n "$i", >> "$pwd/result.csv"
  for e in "${part1_emails[@]}";do
    cd "$pwd/$client_inbox/$e"
    echo "sleep for 5 sec"
    sleep 5
    not_in_cache=$({ time ls -l >/dev/null; } 2>&1)
    echo -n $not_in_cache, >> "$pwd/result.csv"
  done
  echo >> "$pwd/result.csv"
done

echo "part2","1MB","5MB","10MB","15MB" >> "$pwd/result.csv"
for i in {1..5}; do
  echo -n "$i", >> "$pwd/result.csv"
  for e in "${part2_emails[@]}";do
    echo "cd $pwd/$client_inbox/$e"
    cd "$pwd/$client_inbox/$e"
    not_in_cache=$({ time ls -l >/dev/null; } 2>&1)
    echo "sleep for 5 sec"
    sleep 5
    echo -n $not_in_cache, >> "$pwd/result.csv"
  done
  echo >> "$pwd/result.csv"
done
