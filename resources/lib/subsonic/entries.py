"""Build listing-entry dicts (consumed by listing.build_list_item)."""

import time
from datetime import datetime

from . import addon, cache
from .router import url_for

STARRED_COLOUR = "FF00FF00"


def convert_date(iso8601):
    """'2012-04-17T19:53:44' -> '17.04.2012'."""
    if not iso8601:
        return ""
    fmt = "%Y-%m-%dT%H:%M:%S"
    try:
        date_obj = datetime.strptime(iso8601.split(".")[0], fmt)
    except (TypeError, ValueError):
        try:
            date_obj = datetime(*(time.strptime(iso8601.split(".")[0], fmt)[0:6]))
        except ValueError:
            return ""
    return date_obj.strftime("%d.%m.%Y")


def starred_label(item_id, label):
    if cache.is_starred(item_id):
        return "[COLOR=%s]%s[/COLOR]" % (STARRED_COLOUR, label)
    return label


def track_label(item, hide_artist):
    if hide_artist:
        label = item.get("title", "<Unknown>")
    else:
        label = "%s - %s" % (item.get("artist", "<Unknown>"), item.get("title", "<Unknown>"))
    return starred_label(item.get("id"), label)


def album_label(item, hide_artist):
    if hide_artist:
        label = item.get("name", "<Unknown>")
    else:
        label = "%s - %s" % (item.get("artist", "<Unknown>"), item.get("name", "<Unknown>"))
    return starred_label(item.get("id"), label)


# --- capability checks -------------------------------------------------------

def can_star(item_type, item_id):
    # The Subsonic API also stars albums and artists; only tracks are wired up.
    return bool(item_id) and item_type == "track"


def can_download(item_type, item_id):
    return bool(item_id) and item_type in ("track", "album")


def _context_star(item_type, item_id):
    label = addon.L(30034) if cache.is_starred(item_id) else addon.L(30033)
    unstar = cache.is_starred(item_id)
    return (label, "RunPlugin(%s)" % url_for(
        "star_item", type=item_type, ids=item_id, unstar=unstar))


def _context_download(item_type, item_id):
    return (addon.L(30035), "RunPlugin(%s)" % url_for(
        "download_item", type=item_type, id=item_id))


def _context_menu(item_type, item_id):
    menu = []
    if can_star(item_type, item_id):
        menu.append(_context_star(item_type, item_id))
    if can_download(item_type, item_id):
        menu.append(_context_download(item_type, item_id))
    return menu


# --- entry builders --------------------------------------------------------

def playlist_entry(conn, item, params):
    image = conn.getCoverArtUrl(item.get("coverArt"))
    return {
        "label": item.get("name"),
        "thumb": image,
        "fanart": image,
        "url": url_for("list_tracks", playlist_id=item.get("id"),
                       menu_id=params.get("menu_id")),
        "info": {"music": {
            "title": item.get("name"),
            "count": item.get("songCount"),
            "duration": item.get("duration"),
            "date": convert_date(item.get("created")),
        }},
    }


def artist_entry(conn, item, params):
    image = conn.getCoverArtUrl(item.get("coverArt"))
    return {
        "label": starred_label(item.get("id"), item.get("name")),
        "thumb": image,
        "fanart": image,
        "url": url_for("list_albums", artist_id=item.get("id"),
                       menu_id=params.get("menu_id")),
        "info": {"music": {
            "artist": item.get("name"),
            "count": item.get("albumCount"),
        }},
        "context_menu": _context_menu("artist", item.get("id")),
    }


def album_entry(conn, item, params):
    image = conn.getCoverArtUrl(item.get("coverArt"))
    return {
        "label": album_label(item, params.get("hide_artist", False)),
        "thumb": image,
        "fanart": image,
        "url": url_for("list_tracks", album_id=item.get("id"),
                       hide_artist=item.get("hide_artist"),
                       menu_id=params.get("menu_id")),
        "info": {"music": {
            "count": item.get("songCount"),
            "date": convert_date(item.get("created")),
            "duration": item.get("duration"),
            "artist": item.get("artist"),
            "album": item.get("name"),
            "year": item.get("year"),
        }},
        "context_menu": _context_menu("album", item.get("id")),
    }


def track_entry(conn, item, params):
    image = conn.getCoverArtUrl(item.get("coverArt"))
    return {
        "label": track_label(item, params.get("hide_artist")),
        "thumb": image,
        "fanart": image,
        "url": url_for("play_track", id=item.get("id"), menu_id=params.get("menu_id")),
        "is_playable": True,
        "mime": item.get("contentType"),
        "info": {"music": {
            "title": item.get("title"),
            "album": item.get("album"),
            "artist": item.get("artist"),
            "tracknumber": item.get("tracknumber"),
            "year": item.get("year"),
            "genre": item.get("genre"),
            "size": item.get("size"),
            "duration": item.get("duration"),
            "date": item.get("created"),
        }},
        "context_menu": _context_menu("track", item.get("id")),
    }
