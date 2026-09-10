"""Track / album downloading."""

import os
import shutil

import xbmc
import xbmcgui

from . import addon, entries
from .client import get_connection


def download_item(params):
    item_id = params.get("id")
    item_type = params.get("type")

    if not addon.setting("download_folder"):
        addon.notify("Please set a directory for your downloads")
        addon.log_error("No directory set for downloads")

    if not entries.can_download(item_type, item_id):
        return

    if item_type == "track":
        did_action = _download_tracks(item_id)
    elif item_type == "album":
        did_action = _download_album(item_id)
    else:
        did_action = None

    if did_action:
        addon.log("Downloaded %s #%s" % (item_type, item_id))
        addon.notify("Item has been downloaded!")
    else:
        addon.log_error("Unable to download %s #%s" % (item_type, item_id))
    return did_action


def _download_album(album_id):
    conn = get_connection()
    if conn is None:
        return
    album = (conn.getAlbum(album_id) or {}).get("album") or {}
    ids = [track.get("id") for track in album.get("song") or []]
    _download_tracks(ids)


def _download_tracks(ids):
    download_folder = addon.setting("download_folder")
    if not download_folder:
        return

    if not ids:
        return False
    if not isinstance(ids, list) or isinstance(ids, tuple):
        ids = [ids]
    if len(ids) == 0:
        return False

    conn = get_connection()
    if conn is None:
        return

    step = 100 / len(ids)
    parsed = 0
    progress = xbmcgui.DialogProgress()
    progress.create("Downloading tracks...")

    for track_id in ids:
        if progress.iscanceled():
            return False

        track = (conn.getSong(track_id) or {}).get("song")
        pc = parsed * step
        progress.update(int(pc), "Getting track informations...", entries.track_label(track, False))

        relative = track.get("path", None).encode("utf8", "replace")
        track_path = os.path.join(download_folder, relative)
        track_directory = os.path.dirname(os.path.abspath(track_path))

        if os.path.isfile(track_path):
            progress.update(int(pc), "Track has already been downloaded!")
        else:
            progress.update(int(pc), "Downloading track...", track_path)
            try:
                file_obj = conn.download(track_id)
                if not os.path.exists(track_directory):
                    os.makedirs(track_directory)
                handle = open(track_path, "a")
                shutil.copyfileobj(file_obj, handle)
                handle.close()
            except Exception:  # noqa: BLE001
                addon.notify("Error while downloading track #%s" % track_id)

        parsed += 1

    progress.update(100, "Done !", "Enjoy !")
    xbmc.sleep(1000)
    progress.close()
