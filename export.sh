#!/bin/sh -v

wd="/Users/wells/bliss/tech/yogasite/backups"
date=`date '+%Y-%m%d-%H'`
export_py="/Users/wells/bliss/tech/yogasite/backups/export.py"

user="<user>"
pass="<pass>"

$export_py -u $user -p $pass -a yfadmin -o $wd/yf-$date.zip

