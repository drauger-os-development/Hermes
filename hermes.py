#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hermes.py
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
"""Hermes main file"""
import json
import time
import multiprocessing as mp
import sys
import os
import check
import hermes_api as api
import loading_api_response as lar


def flask_runner(argv, pipe):
    """Give Hermes API it's own process"""
    api.init(argv, pipe)
    if api.MODE:
        api.HERMES.run(host="0.0.0.0", debug=api.MODE)
    else:
        api.HERMES.run()


def loading_flask_runner(mode: bool):
    """Give Hermes API it's own process"""
    if mode:
        lar.HERMES.run(host="0.0.0.0", debug=mode)
    else:
        lar.HERMES.run()


def main():
    """main() for Hermes. This mostly just coordinates everything."""
    # Check if running as root as ping3 requires it.
    if os.geteuid() != 0:
        eprint("Please run this script as root!")
        sys.exit(1)
    with open("track.json", "r") as file:
        to_track = json.load(file)
    with open("settings.json", "r") as file:
        settings = json.load(file)
    check_proc = check.UptimeChecker(settings["key_len"])
    # time.sleep(0.001)

    proc = None
    if ("--debug" in sys.argv) or ("-debug" in sys.argv) or ("-d" in sys.argv):
        proc = mp.Process(target=loading_flask_runner, args=(True,))
    else:
        proc = p.Process(target=loading_flask_runner, args=(False,))
    proc.start()


    # Load settings
    response_key = check_proc.send({"SETTINGS": settings})
    response = check_proc.recv(response_key)
    if check_proc.recv(response_key) == "ACCEPTED":
        print("LOADED: SETTINGS")
    else:
        print(f"INVALID RESPONSE: {check_proc.recv(response_key)}")

    # Load tracking info
    response_key = check_proc.send({"TO_TRACK": to_track})
    if check_proc.recv(response_key) == "ACCEPTED":
        print("LOADED: TRACKING INFO")
    else:
        print(f"INVALID RESPONSE: {check_proc.recv(response_key)}")

    # Start tracking
    response_key = check_proc.send("START")
    if check_proc.recv(response_key) == "ACCEPTED":
        print("CHECK PROCESS STARTED!")
    else:
        print(f"INVALID RESPONSE: {check_proc.recv(response_key)}")

    time.sleep(30)

    # Start Flask
    print("Killing Loading Response...")
    start = time.time()
    while True:
        if time.time() > (start + 5):
            proc.terminate()
        if proc.is_alive():
            proc.kill()
        else:
            break
        time.sleep(0.5)
    time.sleep(5)
    print("STARTING FLASK!")
    proc = mp.Process(target=flask_runner, args=(sys.argv, check_proc))
    proc.start()

    # # Check it works
    # print("OBTAINING CACHE!")
    # response_key = check_proc.send("OBTAIN_FULL_CACHE")
    # data = check_proc.recv(response_key)
    # print(json.dumps(data, indent=2))

    time.sleep(900)

    # print("OBTAINING CACHE!")
    # response_key = check_proc.send("OBTAIN_FULL_CACHE")
    # data = check_proc.recv(response_key)
    # print(json.dumps(data, indent=2))
    #
    # # Shutdown
    # check_proc.destruct()
    # print("DESTRUCTED!")


if __name__ == "__main__":
    main()
