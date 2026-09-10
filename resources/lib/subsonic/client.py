"""Subsonic connection, shared by the plugin and the service."""

import libsonic

from . import addon

_connection = None
_failed = False


def get_connection():
    """Return a live ``libsonic.Connection``, or ``None`` after a failed attempt."""
    global _connection, _failed

    if _connection is not None:
        return _connection
    if _failed:
        return None

    try:
        conn = libsonic.Connection(
            baseUrl=addon.setting("subsonic_url"),
            username=addon.setting("username"),
            password=addon.setting("password"),
            port=addon.setting("port"),
            apiVersion=addon.setting("apiversion"),
            insecure=addon.setting_bool("insecure"),
            legacyAuth=addon.setting_bool("legacyauth"),
            useGET=addon.setting_bool("useget"),
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
