#!/bin/bash

### Installitions
apt-get update
apt-get install xz-utils squid isc-dhcp-server python3 python3-pip -y
pip install -r ./requirements.txt

### Make temporary folder
mkdir -p ./.temporary
touch ./.temporary/touchflag
rm -r ./.temporary/*

### Deploy files
OLDPWD=$(pwd)
cd /etc/squid && tar -c ./* | xz -9 > $OLDPWD/squid.default.tar.xz
cd /etc/squid && rm -rf ./*
cd /etc/squid && cp $OLDPWD/squid/* ./ -r
cd /etc/systemd/system && cp $OLDPWD/proxyctl.service
cd /etc/dhcp && cp $OLDPWD/
cd $OLDPWD

### Systemctl's
systemctl daemon-reload
systemctl restart squid.service
systemctl start proxyctl.service
systemctl enable squid.service
systemctl enable proxyctl.service

### Hosts
echo -e "127.0.0.1       proxyctl.org" >> /etc/hosts

### Kernel tweaks
cat sysctl.conf >> /etc/sysctl.conf

### Network configuration
### !!! TOTALLY ACCURATE !!!
# cp etc_network_insterfaces /etc/network/interfaces -f
# cp ifupdown.py /etc/network/ifupdown.py
# chmod 700 /etc/network/ifupdown.py
