#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  main.py
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
import sys
import os
import json
import subprocess as subproc
import shutil
import importlib
import common


def is_running_in_venv() -> bool:
    """Check if we are running in a venv"""
    return hasattr(sys,
                   'real_prefix') or (hasattr(sys,
                                              'base_prefix') and sys.base_prefix != sys.prefix)


def main():
    """Entry point"""
    # Try loading settings
    backup_settings = {
                "venv_name": "venv",
                "fork_if_setup": True,
                "file_list": [each for each in os.listdir() if ".py" == each[-3:]],
                "deps": [],
                "entry_point": {
                            "module": "entry_point",
                            "function": "main"
                        }
            }
    if os.path.exists("settings.json"):
        with open("settings.json", "r") as file:
            settings = json.load(file)
        settings_file = "settings.json"
    else:
        # Settings don't exist. Load internal defaults...'
        common.eprint("WARNING: settings.json not found! Using built-in settings...")
        settings = backup_settings
        settings_file = None

    # Check settings to ensure everything needed is present
    for each in backup_settings:
        if each not in settings:
            print(f"WARNING: {each} not present. Subsituting in-built setting...")
            settings[each] = backup_settings[each]

    if not is_running_in_venv():
        common.eprint(f"{common.Y}Setting up venv...{common.NC}")
        subproc.check_call(["python3", "-m", "venv", settings["venv_name"]])
        cmd = f"bash -c 'source ./{settings['venv_name']}/bin/activate && pip3 install {' '.join(settings['deps'])}'"
        subproc.check_call(cmd, shell=True)

        # Copy this file into venv
        main_dest = "./" + settings["venv_name"] + "/" + sys.argv[0].split("/")[-1]
        shutil.copyfile(sys.argv[0], main_dest)

        # Copy other files into venv
        for each in settings["file_list"]:
            src = "/".join(sys.argv[0].split("/")[:-1]) + f"/{each}"
            dest = "./" + settings["venv_name"] + f"/{each}"
            shutil.copyfile(src, dest)

        if settings_file is not None:
            source = "/".join(sys.argv[0].split("/")[:-1]) + "/" + settings_file
            settings_dest = "./" + settings["venv_name"] + "/" + settings_file
            shutil.copyfile(source, settings_dest)

        common.eprint(f"{common.G}Venv ready!{common.NC}")
        if settings["fork_if_setup"]:
            subproc.Popen([f"./{settings['venv_name']}/bin/python", main_dest])
        else:
            subproc.check_call([f"./{settings['venv_name']}/bin/python", main_dest])
        sys.exit()
    else:
        if not os.path.exists(f"{settings['entry_point']['module']}.py"):
            raise FileNotFoundError(f"{settings['entry_point']['module']}.py does not exist!")
        entry_module = importlib.import_module(settings['entry_point']['module'])
        entry_function = getattr(entry_module, settings["entry_point"]["function"])
        entry_function()

