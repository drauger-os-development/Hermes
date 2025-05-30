#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  check.py
#
#  Copyright 2025 Thomas Castleman <batcastle@draugeros.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""Check URLs for responses"""
import urllib3 as url3
import multiprocessing as mp
import time
import json
import queue
import os
import icmplib as icmp
import comms
import copy
# import threading as mt


def advanced_check(url: str) -> bool:
    """This function is to perform an advanced check. Not all services support this.
       This function will send an HTTP GET request to /status at the designated URL,
       if it receives a JSON response with a 'status': True element, it will assume the service is up and working.
    """
    http = url3.PoolManager()
    if url[-1] == "/":
      data = http.request("GET", f"{url}status")
    else:
      data = http.request("GET", f"{url}/status")
    data = data.data.decode()
    try:
       data = json.loads(data)
    except json.decoder.JSONDecodeError:
       return False
    if "status" in data:
       if data["status"] == True:
          return True
    return False


def simple_check(url: str, wait: int, count: int) -> bool:
    """This function is to perform a simple check. Most services support this.
       This function will send an ICMP PING packet to the designated URL,
       if it receives a response within a given number of seconds, set by `wait`,
       it will assume the service is up and working.
    """
    try:
       data = icmp.ping(url, count=count, timeout=wait)
    except icmp.NameLookupError:
       raise NameError(f"DNS ERROR OR URL NOT VALID: {url}")
    except icmp.SocketPermissionError:
       raise PermissionError("INSUFFICENT PERMISSIONS TO SEND ICMP PACKETS.")
    except icmp.ICMPSocketError:
       return False
    if data.packets_received == 0:
       return False
    if not data.is_alive:
       return False
    return True


def bulk_advanced_check(urls: list) -> dict:
   """Bulk check advanced addresses"""
   results = {}
   for each in urls:
      results[each] = advanced_check(each)
   return results


def bulk_simple_check(urls: list, timeout: int, count: int) -> dict:
   """Bulk check advanced addresses"""
   results = {}
   for each in urls:
      results[each] = simple_check(each, wait=timeout, count=count)
   return results


def cache_gen_handler(pipe) -> None:
   """Handle Generating a new cache"""
   settings = {}
   to_track = {}
   cache = {}
   while True:
      data = pipe.recv()
      if "SETTINGS" in data:
         settings = data["SETTINGS"]
         pipe.send("ACCEPTED")
      elif "TO_TRACK" in data:
         to_track = data["TO_TRACK"]
         pipe.send("ACCEPTED")
      elif data == "START":
         break
   # Check URLS
   for each in to_track:
      cache[each] = {"urls": {}}
      if each != "misc":
         if to_track[each]["type"] == "simple":
            for each1 in to_track[each]["urls"]:
               cache[each]["urls"][each1] = simple_check(each1, settings["icmp"]["timeout"], settings["icmp"]["count"])
         if to_track[each]["type"] == "advanced":
            for each1 in to_track[each]["urls"]:
               cache[each]["urls"][each1] = advanced_check(each1)
         count = 0
         for each1 in to_track[each]["urls"]:
            if not cache[each]["urls"][each1]:
               count += 1
         if count == 0:
            cache[each]["STATUS"] = "UP"
         elif (count > 0) and (count < len(cache[each]["urls"])):
            if to_track[each]["some"] == "single down":
               cache[each]["STATUS"] = [each1 for each1 in cache[each]["urls"] if not cache[each]["urls"][each1]]
            else:
               cache[each]["STATUS"] = to_track[each]["some"].upper()
         elif count == len(cache[each]["urls"]):
            if to_track[each]["all"] == "single down":
               cache[each]["STATUS"] = [each1 for each1 in cache[each]["urls"] if not cache[each]["urls"][each1]]
            else:
               cache[each]["STATUS"] = to_track[each]["all"].upper()
      else:
         del cache["misc"]["urls"]
         for each1 in to_track["misc"]:
            cache["misc"][each1] = {"url": to_track["misc"][each1]["url"]}
            if to_track["misc"][each1]["type"] == "simple":
               cache["misc"][each1]["STATUS"] = simple_check(to_track["misc"][each1]["url"], settings["icmp"]["timeout"],
                                                             settings["icmp"]["count"])
            elif to_track["misc"][each1]["type"] == "advanced":
               cache["misc"][each1]["STATUS"] = advanced_check(to_track["misc"][each1]["url"])
   pipe.send(cache)
   pipe.close()


def cache_gen_spawn(settings: dict, track: dict):
   """Spwan cache_gen_handler() as a seperate process, return the pipe to it"""
   pipe = mp.Pipe()
   proc = mp.Process(target=cache_gen_handler, args=(pipe[0],))
   proc.start()
   pipe = pipe[1]
   pipe.send({"SETTINGS": settings})
   if pipe.recv() == "ACCEPTED":
      pipe.send({"TO_TRACK": track})
   if pipe.recv() == "ACCEPTED":
      pipe.send("START")
   return (pipe, proc)


def check_main(pipe) -> None:
   """This is supposed to run as a seperate thread. Do not call directly!"""
   last = 0
   last_dump = 0
   to_track = {}
   settings = {}
   cache = {}
   new_cache = None
   running = False
   checking = None
   while True:
      to_read = []
      to_read = pipe.has_unread(parent=False)
      pipe.load_messages(parent=False)
      if to_read == []:
         try:
            time.sleep(round(settings["check_freq"] / 20))
         except KeyError:
            time.sleep(3)
      else:
         for each in to_read:
            data = pipe.recv(each)
            if isinstance(data, dict):
               if "TO_TRACK" in data:
                  to_track = data["TO_TRACK"]
                  pipe.send_response(each, "ACCEPTED")
               elif "SETTINGS" in data:
                  settings = data["SETTINGS"]
                  pipe.send_response(each, "ACCEPTED")
               elif "OBTAIN" in data:
                  pipe.send_response(each, cache[data["OBTAIN"]])
            elif isinstance(data, str):
               if data.upper() == "START":
                  if running:
                     pipe.send_response(each, "ALREADY_STARTED")
                  else:
                     if settings == {}:
                        pipe.send_response(each, "CAN NOT START: NO SETTINGS")
                     elif to_track == {}:
                        pipe.send_response(each, "CAN NOT START: NO TRACKING INFO")
                     else:
                        running = True
                        if settings["cache_to_disk"]:
                           if os.path.exists("cache.json"):
                              with open("cache.json", "r") as file:
                                 cache = json.load(file)
                        pipe.send_response(each, "ACCEPTED")
               elif data.upper() == "SHUTDOWN":
                  print("SHUTTING DOWN!")
                  pipe.close(parent=False)
                  if checking is not None:
                     checking[0].close()
                     checking[1].join(timeout=5)
                  if settings["cache_to_disk"]:
                     with open("cache.json", "w") as file:
                        json.dump(cache, file, indent=2)
                  return
               if data.upper() == "OBTAIN_FULL_CACHE":
                  pipe.send_response(each, cache)
               elif data.upper() == "OBTAIN_CATAGORIES":
                  pipe.send_response(each, tuple(cache.keys()))

      ### END OF COMMAND HANDLING

      if "check_freq" in settings:
         if (last + settings["check_freq"]) <= time.time():
            if running:
               if checking is None:
                  checking = cache_gen_spawn(settings, to_track)
               else:
                  if checking[0].poll():
                     try:
                        new_cache = checking[0].recv()
                     except EOFError:
                        continue
                     checking = None
                     last = time.time()

      if new_cache is not None:
         if cache != {}:
            for each in new_cache:
               if each != "misc":
                  if new_cache[each]["STATUS"] == cache[each]["STATUS"]:
                     new_cache[each]["SINCE"] = cache[each]["SINCE"]
                  else:
                     new_cache[each]["SINCE"] = time.time()
               else:
                  for each1 in new_cache["misc"]:
                     if new_cache["misc"][each1]["STATUS"] == cache["misc"][each1]["STATUS"]:
                        new_cache["misc"][each1]["SINCE"] = cache["misc"][each1]["SINCE"]
                     else:
                        new_cache["misc"][each1]["SINCE"] = time.time()
         else:
            for each in new_cache:
               if each != "misc":
                  new_cache[each]["SINCE"] = time.time()
               else:
                  for each1 in new_cache["misc"]:
                     new_cache["misc"][each1]["SINCE"] = time.time()
         cache = copy.deepcopy(new_cache)
         new_cache = None

         if "check_freq" in settings:
            if "cache_to_disk" in settings:
               if settings["cache_to_disk"]:
                  if time.time() >= ((settings["check_freq"] * 3) + last_dump):
                     with open("cache.json", "w") as file:
                        json.dump(cache, file, indent=2)
                     last_dump = time.time()


class UptimeChecker():
   """Handle Checker Info"""
   def __init__(self, key_len: int):
      """Setup and run new process for checking uptime on services."""
      pipe = comms.Duplex(key_len)
      proc = mp.Process(target=check_main, args=(pipe,))
      proc.start()
      self.pipe = pipe
      self.proc = proc
      while not self.proc.is_alive():
         time.sleep(1)

   def send(self, data: any) -> str:
      """Send data to child process"""
      return self.pipe.send(data)

   def recv(self, key: str, block=True, timeout=None) -> any:
      """Send data to child process"""
      self.pipe.load_messages()
      if not block:
         return self.pipe.recv_response(key)
      if timeout is not None:
         start = time.time()
      while True:
         if not self.pipe.load_messages():
            time.sleep(0.5)
         if timeout is not None:
            if (time.time() - start) >= timeout:
               return self.pipe.recv_response(key)
         if self.pipe.recv_response(key) is not None:
            return self.pipe.recv_response(key)
         time.sleep(0.00001)

   def destruct(self) -> bool:
      """Shutdown child process"""
      self.send("SHUTDOWN")
      self.pipe.close()
      self.proc.join(timeout=5)
      del self.pipe, self.proc
      return True
