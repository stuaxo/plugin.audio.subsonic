"""Subsonic connection handling, shared by the plugin and the service.

Failures are classified so the user sees *why* it failed, and a failed attempt
is cached so one invocation shows one notification, not one per action.
"""

import socket
from urllib.error import HTTPError, URLError

import libsonic
from libsonic.errors import AuthError, CredentialError, SonicError, VersionError

from . import addon

_connection = None
_failed = False


def _fail(message):
    global _failed
    _failed = True
    addon.log_error("Subsonic connection failed: %s" % message)
    addon.notify(message)


def get_connection():
    """Return a live ``libsonic.Connection`` or ``None`` (after notifying)."""
    global _connection

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
    except CredentialError:
        _fail(addon.L(30049))  # Username and password are required
        return None
    except Exception as exc:  # noqa: BLE001 - constructor URL parsing etc.
        addon.log_error("Connection setup error: %r" % exc)
        _fail(addon.L(30046))  # Could not connect to the Subsonic server
        return None

    try:
        alive = conn.ping()
    except (AuthError, CredentialError):
        _fail(addon.L(30047))  # Authentication failed - check username/password
        return None
    except VersionError as exc:
        _fail("%s (%s)" % (addon.L(30048), exc))  # Server API version mismatch
        return None
    except HTTPError as exc:
        _fail("%s (HTTP %s)" % (addon.L(30046), exc.code))
        return None
    except (URLError, socket.error) as exc:
        _fail("%s: %s" % (addon.L(30050), getattr(exc, "reason", exc)))  # Cannot reach server
        return None
    except SonicError as exc:
        _fail("%s (%s)" % (addon.L(30046), exc))
        return None

    if not alive:
        _fail(addon.L(30050))  # Cannot reach server
        return None

    _connection = conn
    return conn
