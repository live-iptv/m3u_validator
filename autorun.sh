#!/bin/bash

echo $(dirname $0)

python3 -m pip install requests

cd $(dirname $0)/scripts/

python3 malayalam_m3u.py > ../malayalam_m3u.m3u
python3 tamil_m3u.py > ../tamil_m3u.m3u
python3 xxx_m3u.py > ../xxx_m3u.m3u

echo m3u grabbed
