#!/usr/bin/python3 -u

### Install:
# apt-get install python3-pip
# pip3 install netifaces

import sys
import os
import subprocess
import time
import netifaces

INTERFACES = ['eth1','eth2','eth3','eth4','eth5','eth6']
ACTIONS = ['up','down']
### CHANGE HERE TO YOUR INTERFACE ADDRESS
MAIN_NETWORK = '10.55.55'
MAIN_NETWORK_POSTFIX = '1'

def interface_ip(name, timeout=15):
   ip = ''
   try:
      netifaces.ifaddresses(name)
      for i in range(0,timeout):
         try:
            ip = netifaces.ifaddresses(name)[netifaces.AF_INET][0]['addr']
         except KeyError:
            if i == (timeout - 1):
               print('ERROR: interface "{}" stil have no IPv4 address'.format(name))
               break
            time.sleep(1)
         except Exception as exeption:
            print('ERROR: {}'.format(str(exeption)))
            break
   except ValueError:
      print('ERROR: have no interface "{}"'.format(name))
   except Exception as exeption:
      print('ERROR: {}'.format(str(exeption)))
   return ip

def interface_up(name):
   ip = interface_ip(name)
   if ip == '':
      return -1
   network = ip[:8]
   subprocess.getoutput('ip route add {network}.0/24 dev {name} table rt{name}'.format(network=network,name=name))
   subprocess.getoutput('ip route add default via {network}.1 dev {name} table rt{name}'.format(network=network,name=name))
   subprocess.getoutput('ip route add {main_network}.0/24 dev eth0 src {main_network}.{main_network_postfix} table rt{name}'.format(name=name, main_network=MAIN_NETWORK, main_network_postfix=MAIN_NETWORK_POSTFIX))
   subprocess.getoutput('ip rule add from {network}.0/24 table rt{name}'.format(network=network,name=name))
   subprocess.getoutput('ip rule add to {network}.0/24 table rt{name}'.format(network=network,name=name))
   subprocess.getoutput('iptables -t nat -A POSTROUTING -o {name} -j MASQUERADE'.format(name=name))
   subprocess.getoutput('iptables -t mangle -A POSTROUTING -m ttl --ttl-gt 50 -o {name} -j TTL --ttl-set 65'.format(name=name))
   return 0

def interface_down(name):
   subprocess.getoutput('ip route flush table rt{name}'.format(name=name))
   subprocess.getoutput('iptables -t nat -D POSTROUTING -o {name} -j MASQUERADE'.format(name=name))
   subprocess.getoutput('iptables -t mangle -D POSTROUTING -m ttl --ttl-gt 50 -o {name} -j TTL --ttl-set 65'.format(name=name))
   rule_network = ''
   for i in subprocess.getoutput('ip rule').splitlines():
      if i.find('eth1') >= 0:
         for j in i.split(' '):
            if len(j.split('.')) == 4:
               rule_network = j
   if rule_network != '':
      subprocess.getoutput('ip rule del from {net} table rt{name}'.format(net=rule_network,name=name))
      subprocess.getoutput('ip rule del to {net} table rt{name}'.format(net=rule_network,name=name))
   return 0

def help():
   print("""Usage:\n   {} [ interface_name ] [ up | down ]""".format(sys.argv[0]))

# Check arguments
name = ''
action = ''
try:
   if not sys.argv[1] in INTERFACES:
      print('ERROR: interface "{}" not allowed to this rule'.format(sys.argv[1]))
      exit(-2)
   else:
      name = sys.argv[1]
except:
   print('ERROR: not enouth arguments')
   help()
   exit(-3)
try:
   if not sys.argv[2] in ACTIONS:
      print('ERROR: unknown action "{}"'.format(sys.argv[2]))
      exit(-2)
   else:
      action = sys.argv[2]
except:
   print('ERROR: not enouth arguments')
   help()
   exit(-3)

if action == 'up':
   exit(interface_up(name))
elif action == 'down':
   exit(interface_down(name))

print('ERROR: unknow error. How you fucking went to this?')
help()
exit(-5)