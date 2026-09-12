"""OpenSubsonic connection, shared by the plugin and the service.

libopensonic's synchronous ``Connection`` runs an asyncio event loop on a
background thread and drives every call through it; there is no public,
synchronous way to read the body of a call that returns a raw
``aiohttp.ClientResponse`` (cover art, downloads). ``_read(conn, response)``
below schedules that read back onto the connection's own loop via its
private ``_loop`` attribute - the only way to do it with this library's
public surface.
"""

import asyncio
import hashlib
import os

import xbmcvfs
import libopensonic

from . import addon

_connection = None
_failed = False

_ART_CACHE_DIR = os.path.join(addon.ADDON_PROFILE, "artcache")


def get_connection():
    """Return a live ``libopensonic.Connection``, or ``None`` after a failed attempt."""
    global _connection, _failed

    if _connection is not None:
        return _connection
    if _failed:
        return None

    api_key = addon.setting("api_key")
    try:
        conn = libopensonic.Connection(
            base_url=addon.setting("subsonic_url"),
            username=None if api_key else addon.setting("username"),
            password=None if api_key else addon.setting("password"),
            port=int(addon.setting("port") or 4040),
            api_key=api_key or None,
            api_version=addon.setting("apiversion"),
            legacy_auth=addon.setting_bool("legacyauth"),
            use_get=True,  # a fully self-contained URL, for Kodi's player to resolve
        )
        alive = conn.ping()
    except Exception:  # noqa: BLE001
        alive = False

    if not alive:
        _failed = True
        addon.notify("Connection error")
        return None

    _connection = conn
    return conn


def cleanup():
    """Stop the connection's background event loop, if one was started."""
    global _connection
    if _connection is not None:
        _connection.cleanup()
        _connection = None


def _read(conn, response):
    """Read an aiohttp ClientResponse's full body on the connection's own loop."""
    return asyncio.run_coroutine_threadsafe(response.read(), conn._loop).result()


def download_bytes(conn, song_id):
    return _read(conn, conn.download(song_id))


def art_path(conn, cover_art_id, size=None):
    """Return a local file path for a cover art id, fetching and caching it on
    first use. Returns "" if there is no art or the fetch fails.
    """
    if not cover_art_id:
        return ""

    key = hashlib.md5(("%s:%s" % (cover_art_id, size)).encode("utf-8")).hexdigest()
    path = os.path.join(_ART_CACHE_DIR, key + ".img")

    if xbmcvfs.exists(path):
        return path

    try:
        data = _read(conn, conn.get_cover_art(cover_art_id, size))
    except Exception as exc:  # noqa: BLE001
        addon.log_error("could not fetch cover art %s: %r" % (cover_art_id, exc))
        return ""

    if not xbmcvfs.exists(_ART_CACHE_DIR):
        xbmcvfs.mkdirs(_ART_CACHE_DIR)
    with xbmcvfs.File(path, "w") as handle:
        handle.write(bytearray(data))
    return path
