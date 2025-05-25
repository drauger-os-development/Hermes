#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hermes_api.py
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
"""Provide REST API to retreive statuses"""
from flask import Flask, request, redirect, render_template, send_from_directory, url_for

HERMES = Flask(__name__)
MODE = False
PIPE = None


def init(argv, pipe):
    global MODE
    global PIPE
    if ("--debug" in argv) or ("-debug" in argv) or ("-d" in argv):
        MODE = True
    PIPE = pipe

@HERMES.errorhandler(404)
def error_404(e):
    """Catch Error 404"""
    return page_not_found()


@HERMES.errorhandler(403)
def error_403(e):
    """Catch Error 403"""
    return forbidden()


@HERMES.errorhandler(418)
def error_418(e):
    """Catch Error 418 (Should never happen)"""
    return i_am_a_teapot()


@HERMES.errorhandler(500)
def error_500(e):
    """Catch Error 500"""
    return internal_error()


@HERMES.route("/404")
def page_not_found():
    """Error 404 Page"""
    return {"STATUS": 404,
            "MESSAGE": "NOT FOUND"}


@HERMES.route("/403")
def forbidden():
    """Error 403 Page"""
    return {"STATUS": 403,
            "MESSAGE": "FORBIDDEN"}


@HERMES.route("/418")
def i_am_a_teapot():
    """Error 418 Easter Egg Page"""
    return {"STATUS": 418,
            "MESSAGE": "I AM A TEAPOT"}


@HERMES.route("/500")
def internal_error():
    """Error 500 Page"""
    return {"STATUS": 500,
            "MESSAGE": "INTERNAL ERROR"}


@HERMES.route("/")
def root():
    """Root directory"""
    global PIPE
    PIPE.send("OBTAIN_FULL_CACHE")
    possible_nodes = PIPE.recv()
    print("RETREIVED POSSIBLE NODES!")
    output = {"STATUS": 200,
              "NODES": possible_nodes}
    return output

