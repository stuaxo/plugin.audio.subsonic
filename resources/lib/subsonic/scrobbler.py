"""Last.fm scrobbling service.

A short poll that submits a "now playing" notification when a Subsonic track
starts and a real scrobble once it passes the halfway point. The ``scrobble``
setting is re-read every tick.
"""

import re

import xbmc

from . import addon
from .client import get_connection

# The resolved item keeps its original plugin:// path in Filenameandpath.
_ID_RE = re.compile(r"[?&]action=play_track&id=([^&]+)")
_SCROBBLE_AT = 0.5
_POLL_SECONDS = 5


def _scrobble(track_id, submission):
    conn = get_connection()
    if conn is None:
        return False
    try:
        return conn.scrobble(track_id, submission=submission).get("status") == "ok"
    except Exception as exc:  # noqa: BLE001
        addon.log_error(
            "scrobble(%s, submission=%s) failed: %r" % (track_id, submission, exc)
        )
        return False


def _current_track_id(player):
    for path in (xbmc.getInfoLabel("Player.Filenameandpath"), _playing_file(player)):
        match = _ID_RE.search(path or "")
        if match:
            return match.group(1)
    return None


def _playing_file(player):
    try:
        return player.getPlayingFile()
    except RuntimeError:
        return ""


def main():
    monitor = xbmc.Monitor()
    player = xbmc.Player()
    current = None
    scrobbled = False
    addon.log("scrobble service started")

    while not monitor.waitForAbort(_POLL_SECONDS):
        if not player.isPlayingAudio() or not addon.setting_bool("scrobble"):
            current, scrobbled = None, False
            continue

        track_id = _current_track_id(player)
        if not track_id:
            continue

        if track_id != current:
            current, scrobbled = track_id, False
            _scrobble(track_id, submission=False)  # now playing

        if not scrobbled:
            try:
                total, position = player.getTotalTime(), player.getTime()
            except RuntimeError:
                continue
            if total > 0 and position / total >= _SCROBBLE_AT:
                scrobbled = _scrobble(track_id, submission=True)

    addon.log("scrobble service stopped")
