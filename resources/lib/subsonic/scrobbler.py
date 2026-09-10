"""Last.fm scrobbling service."""

import re

import xbmc

from . import addon
from .client import get_connection

_PATTERN = re.compile(r"plugin://plugin\.audio\.subsonic/\?action=play_track&id=(.*?)&")


def _scrobble_track(track_id):
    conn = get_connection()
    if conn is None:
        return False
    result = conn.scrobble(track_id)
    if result["status"] == "ok":
        addon.notify("Scrobbled track")
        return True
    addon.notify("Scrobble failed")
    return False


def main():
    if not addon.setting_bool("scrobble"):
        xbmc.log("Subsonic service not started due to settings", xbmc.LOGINFO)
        return

    monitor = xbmc.Monitor()
    xbmc.log("Subsonic service started", xbmc.LOGINFO)
    addon.notify("Subsonic service started")
    scrobbled = False

    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            break
        if not xbmc.getCondVisibility("Player.HasMedia"):
            continue
        try:
            name = xbmc.getInfoLabel("Player.Filenameandpath")
            progress = xbmc.getInfoLabel("Player.Progress")
            track_id = re.findall(_PATTERN, name)[0]
            if int(progress) < 50:
                scrobbled = False
            elif int(progress) >= 50 and not scrobbled:
                if _scrobble_track(track_id):
                    scrobbled = True
        except IndexError:
            scrobbled = True
        except Exception as exc:  # noqa: BLE001
            xbmc.log("Subsonic service failed %s" % exc, xbmc.LOGINFO)
