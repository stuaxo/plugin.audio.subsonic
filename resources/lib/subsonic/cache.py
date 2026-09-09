"""Starred-track cache: a JSON file in the profile dir with a TTL from the
``cachetime`` setting (minutes). Invalidated on star/unstar.
"""

import json
import os
import time

from . import addon
from .client import get_connection

_CACHE_FILE = os.path.join(addon.ADDON_PROFILE, "starred.json")
_mem = None  # {"ids": [...] | None, "updated": <epoch>}


def _read():
    try:
        with open(_CACHE_FILE, encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and isinstance(data.get("ids"), list):
            return data
    except (OSError, ValueError):
        pass
    return {"ids": None, "updated": 0}


def _write(data):
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
    except OSError as exc:
        addon.log_error("Could not write starred cache: %r" % exc)


def _fetch(conn):
    response = conn.getStarred()
    songs = (response.get("starred") or {}).get("song") or []
    return [song["id"] for song in songs if song.get("id")]


def starred_ids(force=False):
    """Return the set of starred track ids, refreshing past the TTL."""
    global _mem

    if _mem is None:
        _mem = _read()

    ttl = addon.setting_int("cachetime", 60) * 60
    fresh = _mem["ids"] is not None and (time.time() - _mem["updated"]) < ttl
    if fresh and not force:
        return set(_mem["ids"])

    conn = get_connection()
    if conn is None:
        return set(_mem["ids"] or [])

    try:
        ids = _fetch(conn)
    except Exception as exc:  # noqa: BLE001 - fall back to the stale set
        addon.log_error("Could not refresh starred cache: %r" % exc)
        return set(_mem["ids"] or [])

    _mem = {"ids": ids, "updated": time.time()}
    _write(_mem)
    return set(ids)


def is_starred(item_id):
    return item_id in starred_ids()


def seed(ids):
    """Populate the cache from an already-fetched starred list (no API call)."""
    global _mem
    _mem = {"ids": [i for i in ids if i], "updated": time.time()}
    _write(_mem)


def invalidate():
    """Drop the cache so the next read re-fetches (call after star/unstar)."""
    global _mem
    _mem = None
    try:
        os.remove(_CACHE_FILE)
    except OSError:
        pass
