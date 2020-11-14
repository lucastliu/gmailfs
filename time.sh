#!/bin/bash
echo "part1 perf test"
pwd=`pwd`
client_inbox="client/inbox"
src_inbox="src/inbox"
declare -a part1_emails=("hey ID 175a51ddd82e5c1a" 'Long email test ID 17519a4cd78744f9' "test from bletsch ID 17589c9906a2afff", "hey ID 175a51ddd82e5c1a")
declare -a part2_emails=("1MB ID 175c07cb69deb952" "5MB ID 175c082bdd62567a" "10MB ID 175c0833dd194bf3" "15MB ID 175c083ab107a95c")
for e in "${part1_emails[@]}";do
  if [[ -d "$path/$e" ]]
  then
      echo "$e shouldn't be in cache folder now"
      exit 1
  fi
done

TIMEFORMAT=%R
get_time="not_in_cache=$({ time ls -l >/dev/null; } 2>&1);in_cache=$({ time ls -l >/dev/null; } 2>&1);"

echo "[PART 1]"

echo "part1","plain txt","wikipedia page","5M attachment" >> "$pwd/result.csv"
for i in {1..5}; do
  echo -n "$i", >> "$pwd/result.csv"
  for e in "${part1_emails[@]}";do
    cd "$pwd/$src_inbox/$e"
    not_in_cache=$({ time ls -l >/dev/null; } 2>&1)
    echo -n $not_in_cache, >> "$pwd/result.csv"
  done
  echo >> "$pwd/result.csv"
done

echo "part2","1MB","5MB","10MB","15MB" >> "$pwd/result.csv"
for i in {1..5}; do
  echo -n "$i", >> "$pwd/result.csv"
  for e in "${part2_emails[@]}";do
    cd "$pwd/$src_inbox/$e"
    not_in_cache=$({ time ls -l >/dev/null; } 2>&1)
    echo -n $not_in_cache, >> "$pwd/result.csv"
  done
  echo >> "$pwd/result.csv"
done
