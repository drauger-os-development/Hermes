#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  comms.py
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
"""process-safe and thread-safe duplex communication based on the Queue lib"""
import queue
import multiprocessing as mp
import time
import copy
import random
import common


def make_key(key_length: int) -> str:
    """Generate a random string that follows these rules:
    - Arbitrary length
    - should be a randomly generated string of letters and numbers
    - Have no special characters
    """
    remaining_len = key_length
    allowed_letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    allowed_numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    suffix = []
    while remaining_len > 0:
        if (random.randint(0, 10) % 2) == 0:
            # letter
            if (random.randint(0, 10) % 2) == 0:
                # Uppercase
                suffix.append(random.sample(allowed_letters, 1)[0])
            else:
                # Lowercase
                suffix.append(random.sample(allowed_letters, 1)[0].lower())
        else:
            # number
            suffix.append(str(random.sample(allowed_numbers, 1)[0]))
        remaining_len -= 1
    suffix = "".join(suffix)
    return suffix


class Duplex():
    """Duplex Communiction between two processes"""
    def __init__(self, key_len: int):
        """Initalization"""
        self.key_len = key_len
        self.parent_to_child = mp.Queue()
        self.child_to_parent = mp.Queue()
        self.responded = []

        self.log = {}

        self.log_addition_template = {
                "message": None,
                "read": False,
                "timestamps": {
                        "creation": 0,
                        "accessed": 0,
                        "modified": 0
                    },
                "from_parent": True,
                "response": None
            }

    def send(self, message: any, parent: bool=True) -> str:
        """Send a message to other process"""
        add = copy.copy(self.log_addition_template)
        add["message"] = message
        add["timestamps"]["creation"] = time.time()
        add["timestamps"]["accessed"] = time.time()
        add["timestamps"]["modified"] = time.time()
        while True:
            key = make_key(self.key_len)
            if key not in self.log:
                break
        if not parent:
            add["from_parent"] = False
        self.log[key] = add
        if parent:
            self.parent_to_child.put(self.log)
        else:
            self.child_to_parent.put(self.log)
        return key

    def send_response(self, key: str, message: any) -> bool:
        """Respond to a previous message"""
        update = copy.copy(self.log[key])
        add = copy.copy(self.log_addition_template)
        add["message"] = message
        add["timestamps"]["creation"] = time.time()
        add["timestamps"]["accessed"] = time.time()
        add["timestamps"]["modified"] = time.time()
        add["from_parent"] = not update["from_parent"]
        update["response"] = add
        update["timestamps"]["accessed"] = time.time()
        update["timestamps"]["modified"] = time.time()
        self.log.update({key: update})
        if add["from_parent"]:
            self.parent_to_child.put(self.log)
        else:
            self.child_to_parent.put(self.log)

    def load_messages(self, parent=True) -> None:
        """Load new messages from queues into log
           Returns True if new messages available, False otherwise.
        """
        if not parent:
            while not self.parent_to_child.empty():
                self.log.update(self.parent_to_child.get_nowait())
        else:
            while not self.child_to_parent.empty():
                self.log.update(self.child_to_parent.get_nowait())


    def recv(self, key: str) -> any:
        """Receive a message from other process"""
        self.log[key]["read"] = True
        self.log[key]["timestamps"]["accessed"] = time.time()
        self.responded.append(key)
        return self.log[key]["message"]

    def get_timestamps(self, key: str) -> float:
        """Return the timestamp of a message"""
        return self.log[key]["timestamps"]

    def recv_response(self, key: str, parent: bool=True) -> any:
        """Receive a message from other process"""
        try:
            self.log[key]["response"]["read"] = True
            self.log[key]["response"]["timestamps"]["accessed"] = time.time()
        except TypeError:
            return None
        except KeyError:
            return None
        return self.log[key]["response"]["message"]

    def has_unread(self, parent=True) -> list:
        """Check for unread messages"""
        keys = []
        for each in self.log:
            if (parent ^ self.log[each]["from_parent"]):
                if not self.log[each]["read"]:
                    if self.log[each]['response'] is None:
                        keys.append(each)
                    else:
                        self.log[each]["read"] = True
        keys = common.unique(keys)
        return keys

    def close(self, parent=True) -> None:
        """Close all Queues"""
        if parent:
            self.parent_to_child.close()
        else:
            self.child_to_parent.close()
