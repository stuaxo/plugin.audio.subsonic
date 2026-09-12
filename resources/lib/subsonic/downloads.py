"""Track / album downloading."""

import os

import xbmc
import xbmcgui
import xbmcvfs

from . import addon, client, entries


def download_item(params):
    item_id = params.get("id")
    item_type = params.get("type")

    if not addon.setting("download_folder"):
        addon.notify("Please set a directory for your downloads")
        addon.log_error("No directory set for downloads")

    if not entries.can_download(item_type, item_id):
        return

    if item_type == "track":
        did_action = _download_tracks([item_id])
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
    conn = client.get_connection()
    if conn is None:
        return False
    ids = [track.id for track in conn.get_album(album_id).song or []]
    return _download_tracks(ids)


def _download_tracks(ids):
    ids = [i for i in ids if i]
    download_folder = addon.setting("download_folder")
    if not download_folder or not ids:
        return False

    conn = client.get_connection()
    if conn is None:
        return False

    step = 100 / len(ids)
    progress = xbmcgui.DialogProgress()
    progress.create("Downloading tracks...")

    for parsed, track_id in enumerate(ids):
        if progress.iscanceled():
            return False

        track = conn.get_song(track_id)
        pc = int(parsed * step)
        progress.update(pc, "Getting track informations...", entries.track_label(track, False))

        track_path = os.path.join(download_folder, track.path)
        track_directory = os.path.dirname(track_path)

        if xbmcvfs.exists(track_path):
            progress.update(pc, "Track has already been downloaded!")
            continue

        progress.update(pc, "Downloading track...", track_path)
        try:
            data = client.download_bytes(conn, track_id)
            if track_directory and not xbmcvfs.exists(track_directory):
                xbmcvfs.mkdirs(track_directory)
            with xbmcvfs.File(track_path, "w") as handle:
                handle.write(bytearray(data))
        except Exception as exc:  # noqa: BLE001
            addon.notify("Error while downloading track #%s" % track_id)
            addon.log_error("download %s failed: %r" % (track_id, exc))

    progress.update(100, "Done !", "Enjoy !")
    xbmc.sleep(1000)
    progress.close()
    return True
