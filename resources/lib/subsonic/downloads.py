"""Track/album downloading via xbmcvfs."""

import os

import xbmcgui
import xbmcvfs

from . import addon
from .client import get_connection
from .library import get_song

_CHUNK = 256 * 1024


def download_item(params):
    item_type = params.get("type")
    item_id = params.get("id")

    folder = addon.setting("download_folder")
    if not folder:
        addon.notify(addon.L(30052))  # Set a download folder in the settings first
        return

    conn = get_connection()
    if conn is None:
        return

    if item_type == "track":
        ids = [item_id]
    elif item_type == "album":
        album = (conn.getAlbum(item_id) or {}).get("album") or {}
        ids = [song["id"] for song in album.get("song") or [] if song.get("id")]
    else:
        return

    _download_tracks(conn, ids, folder)


def _download_tracks(conn, ids, folder):
    ids = [track_id for track_id in ids if track_id]
    if not ids:
        return

    progress = xbmcgui.DialogProgress()
    progress.create(addon.L(30053))  # Downloading
    total = len(ids)
    errors = 0

    for index, track_id in enumerate(ids):
        if progress.iscanceled():
            break

        song = get_song(conn, track_id) or {}
        relative = song.get("path") or "%s.%s" % (track_id, song.get("suffix", "mp3"))
        destination = os.path.join(folder, relative.replace("\\", "/"))

        progress.update(
            int(index * 100 / total),
            "%s - %s" % (song.get("artist", ""), song.get("title", relative)),
        )

        if xbmcvfs.exists(destination):
            continue

        parent = os.path.dirname(destination)
        if parent and not xbmcvfs.exists(parent):
            xbmcvfs.mkdirs(parent)

        if not _fetch(conn, track_id, destination):
            errors += 1

    progress.close()
    if errors:
        addon.notify(addon.L(30054) % errors)  # %d track(s) could not be downloaded
    else:
        addon.notify(addon.L(30055))  # Download complete


def _fetch(conn, track_id, destination):
    try:
        source = conn.download(track_id)
        with xbmcvfs.File(destination, "w") as out:
            while True:
                chunk = source.read(_CHUNK)
                if not chunk:
                    break
                out.write(bytearray(chunk))
        return True
    except Exception as exc:  # noqa: BLE001
        addon.log_error("download %s failed: %r" % (track_id, exc))
        xbmcvfs.delete(destination)
        return False
