"""Starred-track cache: a JSON file in the profile dir with a TTL from the
``cachetime`` setting (minutes).
"""

import json
import os
import time

from . import addon
from .client import get_connection
from .library import walk_tracks_starred

_CACHE_FILE = os.path.join(addon.ADDON_PROFILE, "starred.json")
_ids = None
_updated = 0


def _load():
    global _ids, _updated
    try:
        with open(_CACHE_FILE, encoding="utf-8") as handle:
            data = json.load(handle)
        _ids = list(data["ids"])
        _updated = data["updated"]
    except (OSError, ValueError, KeyError, TypeError):
        _ids, _updated = [], 0


def _save():
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as handle:
            json.dump({"ids": _ids, "updated": _updated}, handle)
    except OSError as exc:
        addon.log_error("could not write starred cache: %r" % exc)


def refresh(forced=False):
    global _ids, _updated
    if _ids is None:
        _load()

    ttl = addon.setting_int("cachetime", 60) * 60
    if not forced and time.time() - _updated < ttl:
        return

    conn = get_connection()
    if conn is None:
        return

    _ids = [song.get("id") for song in walk_tracks_starred(conn) if song.get("id")]
    _updated = time.time()
    _save()


def is_starred(item_id):
    refresh()
    return item_id in (_ids or [])
