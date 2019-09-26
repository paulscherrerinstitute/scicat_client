#!/bin/bash

pgroups="p16581 p16582 p16583 p17245 p17296 p17295 p17536 p17569 p17571"

echo "PGROUP SAVED NOTSAVED"
for pgroup in $(echo $pgroups | sort ); do
    python scicat_client.py dump_filelist -g $pgroup > filelist_${pgroup}.txt
    python check_saved_data.py $pgroup /sf/alvra/data/$pgroup filelist_$pgroup.txt > \
           filelist_notsavedh5_$pgroup.txt 
    python check_saved_data.py $pgroup /sf/bernina/data/$pgroup filelist_$pgroup.txt >> \
           filelist_notsavedh5_$pgroup.txt

    saved=$(wc -l filelist_$pgroup.txt | awk '{print $1}')
    notsaved=$(wc -l filelist_notsavedh5_$pgroup.txt | awk '{print $1}')
    echo $pgroup $saved $notsaved
done

