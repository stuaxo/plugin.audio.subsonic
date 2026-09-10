"""Starred-track cache.

``local_starred`` holds the ids for the current invocation; the pickle store
persists them across invocations with a TTL from the ``cachetime`` setting
(minutes).
"""

import time

from . import addon
from .client import get_connection
from .library import walk_tracks_starred
from .storage import Storage

local_starred = []


def refresh(forced=False):
    global local_starred
    ttl = addon.setting_int("cachetime", 60) * 60
    with Storage() as store:
        last_update = store.get("updated", 0)
        if forced or time.time() - ttl > last_update:
            conn = get_connection()
            if conn is not None:
                ids = [song.get("id") for song in walk_tracks_starred(conn)]
                store["starred_ids"] = ids
                store["updated"] = time.time()
                local_starred = ids
        if not local_starred:
            local_starred = store.get("starred_ids", [])


def starred_ids():
    refresh()
    return local_starred


def is_starred(item_id):
    return item_id in starred_ids()
