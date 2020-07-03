#!/bin/bash

UUID=$(cat /proc/sys/kernel/random/uuid)
timestamp=$(date +"%Y/%m/%d/%H%M%S")

celcius=$(tail -n 1 /sys/bus/w1/devices/28-00000b1fa3b0/w1_slave | awk -F'=' '{print $2/1000}')
fahrenheit=$(awk -v c="$celcius" 'BEGIN {print c * 9/5 + 32}')

json="{\"timestamp\": $(date +'%s'), \"celcius\": $celcius, \"fahrenheit\": $fahrenheit}"

touch /tmp/$UUID
echo $json > /tmp/$UUID
/usr/local/bin/aws s3api put-object --profile iot-s3-writer --region us-east-2 --bucket BUCKETNAME --key "pool/${timestamp}.json" --body /tmp/$UUID
rm /tmp/$UUID