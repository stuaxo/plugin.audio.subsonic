"""Minimal plugin router: action registration, ``plugin://`` URL building,
the plugin handle, and query-string dispatch.
"""

import sys
from urllib.parse import parse_qsl, urlencode

from . import addon

_ACTIONS = {}

# sys.argv is ["plugin://plugin.audio.subsonic/", "<handle>", "?<query>"]
BASE_URL = sys.argv[0] if sys.argv else "plugin://%s/" % addon.ADDON_ID
HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1


def action(name=None):
    """Decorator registering a view under ``name`` (default: its function name)."""

    def decorator(func):
        key = name or func.__name__
        if key in _ACTIONS:
            raise RuntimeError("Duplicate action: %s" % key)
        _ACTIONS[key] = func
        return func

    return decorator


def url_for(action_name, **kwargs):
    """Build a ``plugin://`` URL for ``action_name`` with query params."""
    kwargs["action"] = action_name
    return "{0}?{1}".format(BASE_URL, urlencode(kwargs, doseq=True))


def run():
    params = dict(parse_qsl(sys.argv[2].lstrip("?"))) if len(sys.argv) > 2 else {}
    handler = _ACTIONS.get(params.get("action", "root"))
    if handler is None:
        addon.log_error("Unknown action: %s" % params.get("action"))
        raise RuntimeError("Unknown action: %s" % params.get("action"))
    handler(params)
