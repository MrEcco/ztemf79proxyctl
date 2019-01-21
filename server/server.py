#!/usr/bin/python3 -u

### Install:
# apt-get install python3-pip
# pip3 install requests
# pip3 install json
# pip3 install urllib

import os, sys, subprocess
import threading
import json
import time
import requests
from urllib.parse import urlparse
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

### ONLY FOR ZTE MF79 (may be with RU firmware)

ADDRESS_TEMPLATE = '172.30.{}.1'

class HTTPHandler(BaseHTTPRequestHandler):
   server_version = "nginx"

   # Lock requiests logging
   # def log_message(self, format, *args):
   #    return

   def do_GET(self):
      status = ""
      code = 500
      if self.path[:5] == "/ping":
         status = "{'ping':'pong'}"
         code = 200
      elif self.path[:9] == "/api/ping":
         status = "{'ping':'pong'}"
         code = 200
      elif self.path[:11] == "/api/status":
         retobj = {'devices':[]}
         def set_status(num, address):
            retobj['devices'].append({'id':str(num),'status':get_status(address)})
         routines = [threading.Thread(target=set_status, args=(i, ADDRESS_TEMPLATE.format(i))) for i in range(1,7)]
         for i in routines:
            i.start()
         for i in routines:
            i.join()
         status = json.dumps(retobj)
         code = 200
      elif self.path[:11] == "/api/start?":
         modem = self.get_modem_num(self.path)
         status = ""
         if modem > 0:
            if start(ADDRESS_TEMPLATE.format(modem)) == 'OK':
               code = 200
            else:
               code = 400
         else:
            code = 404
      elif self.path[:10] == "/api/stop?":
         modem = self.get_modem_num(self.path)
         status = ""
         if modem > 0:
            if stop(ADDRESS_TEMPLATE.format(modem)) == 'OK':
               code = 200
            else:
               code = 400
         else:
            code = 404
      elif self.path == "/":
         self.send_response(200)
         self.send_header('Content-type', 'text/html')
         self.end_headers()
         self.wfile.write(str(get_file_content(os.path.join('public','index.html'))).encode('utf-8'))
         return
      elif self.path[:12] == "/api/restart":
         restart_after(3)
         status = ""
         code = 200
      else:
         tryfile = ""
         if self.path[:1] == os.sep:
            tryfile = os.path.join("public", os.path.normpath(self.path[1:]))
         else:
            tryfile = os.path.join("public", os.path.normpath(self.path))
         print(tryfile)
         if os.path.isfile(tryfile):
            self.send_response(200)
            if tryfile[-4:] == '.css':
               self.send_header('Content-type', 'text/css')
            elif tryfile[-3:] == '.js':
               self.send_header('Content-type', 'application/javascript')
            elif tryfile[-5:] == '.html':
               self.send_header('Content-type', '       text/html')
            else:
               self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(get_file_content(tryfile)).encode('utf-8'))
            return
         else:
            status = ""
            code = 404
      self.send_response(code)
      self.send_header('Content-type', 'text/plain')
      self.send_header('Access-Control-Allow-Origin', '*')
      self.end_headers()
      self.wfile.write(str(status).encode('utf-8'))

   def get_modem_num(self, path):
     keys = parse_qs(urlparse("https://test.com" + path).query)
     try:
        num = int(keys['id'][0])
        if num <=6 and num >= 1:
           return num
        else:
           return -1
     except:
        return -255

def login(address):
   template = "http://" + address + "/goform/goform_set_cmd_process"
   headers = { 'Accept': 'application/json, text/javascript, */*; q=0.01', 'Cache-Control':'no-cache', 'Host': address, 'Pragma': 'no-cache', 'Referer': 'http://' + address + '/index.html', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest' }
   # usrlencode(base64(password))
   # 'admin' is default
   data = 'isTest=false&goformId=LOGIN&password=YWRtaW4%3D'
   try:
      received = json.loads(requests.post(template, data=data, headers=headers, timeout=5).text)
      if received['result'] == '0':
         return 'OK'
      else:
         return 'FAIL'
   except:
      return 'REQUEST_ERROR'

def restart_routine(timeout):
   time.sleep(timeout)
   # print('subprocess.getoutput(/sbin/reboot) in thread')
   subprocess.getoutput('/sbin/reboot')

def restart_after(timeout):
   routine = threading.Thread(target=restart_routine, args=(timeout,))
   routine.start()

def get_status(address):
   template = "http://" + address + "/goform/goform_get_cmd_process?multi_data=1&isTest=false&sms_received_flag_flag=0&sts_received_flag_flag=0&sms_db_change_flag=0&cmd=ppp_status&_=" + str(time.time())
   headers = { 'Accept': 'application/json, text/javascript, */*; q=0.01', 'Cache-Control':'no-cache', 'Host': address, 'Pragma': 'no-cache', 'Referer': 'http://' + address + '/index.html', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest' }
   try:
      received = json.loads(requests.get(template, headers=headers, timeout=0.2).text)
      if received['ppp_status'] == 'ppp_disconnected':
         return 'DISCONNECTED'
      elif received['ppp_status'] == 'ppp_connected':
         return 'CONNECTED'
      else:
         return 'UNKNOWN'
   except requests.ConnectTimeout:
      return 'UNKNOWN'
   except:
      return 'REQUEST_ERROR'

def start(address):
   template = "http://" + address + "/goform/goform_set_cmd_process"
   headers = { 'Accept': 'application/json, text/javascript, */*; q=0.01', 'Cache-Control':'no-cache', 'Host': address, 'Pragma': 'no-cache', 'Referer': 'http://' + address + '/index.html', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest' }
   data = 'isTest=false&notCallback=true&goformId=CONNECT_NETWORK'
   try:
      received = json.loads(requests.post(template, data=data, headers=headers, timeout=3).text)
      if received['result'] == 'success':
         return 'OK'
      else:
         return 'UNKNOWN'
   except:
      return 'REQUEST_ERROR'

def stop(address):
   template = "http://" + address + "/goform/goform_set_cmd_process"
   headers = { 'Accept': 'application/json, text/javascript, */*; q=0.01', 'Cache-Control':'no-cache', 'Host': address, 'Pragma': 'no-cache', 'Referer': 'http://' + address + '/index.html', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest' }
   data = 'isTest=false&notCallback=true&goformId=DISCONNECT_NETWORK'
   try:
      received = json.loads(requests.post(template, data=data, headers=headers, timeout=3).text)
      if received['result'] == 'success':
         return 'OK'
      else:
         return 'UNKNOWN'
   except:
      return 'REQUEST_ERROR'

def run_loginer_routine():
   while True:
      for i in range(1,7):
         login(ADDRESS_TEMPLATE.format(i))
      time.sleep(30)

def run_loginer():
   routine = threading.Thread(target=run_loginer_routine, args=())
   routine.start()

def get_file_content(filename):
   try:
      with open(os.path.normpath(filename), "r") as fd:
         return str(fd.read())
   except Exception as e:
      print(e)
      return

def run_backend(port=80):
   httpd = HTTPServer(('127.0.0.1', port), HTTPHandler)
   httpd.serve_forever()
   httpd.server_close()

run_loginer()
run_backend()
