"""Build listing-entry dicts (consumed by listing.build_list_item)."""

from . import addon, cache
from .client import art_path
from .router import url_for

STARRED_COLOUR = "FF00FF00"


def _get(item, name, default=None):
    """getattr with a default - call sites see a mix of media_types classes
    (e.g. search2's albums are Child objects, not AlbumID3) that don't all
    carry the same fields.
    """
    return getattr(item, name, None) or default


def _album_name(item):
    return _get(item, "name") or _get(item, "title", "<Unknown>")


def starred_label(item_id, label):
    if cache.is_starred(item_id):
        return "[COLOR=%s]%s[/COLOR]" % (STARRED_COLOUR, label)
    return label


def track_label(item, hide_artist):
    if hide_artist:
        label = _get(item, "title", "<Unknown>")
    else:
        label = "%s - %s" % (_get(item, "artist", "<Unknown>"), _get(item, "title", "<Unknown>"))
    return starred_label(item.id, label)


def album_label(item, hide_artist):
    if hide_artist:
        label = _album_name(item)
    else:
        label = "%s - %s" % (_get(item, "artist", "<Unknown>"), _album_name(item))
    return starred_label(item.id, label)


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
    image = art_path(conn, item.cover_art)
    return {
        "label": item.name,
        "thumb": image,
        "fanart": image,
        "url": url_for("list_tracks", playlist_id=item.id, menu_id=params.get("menu_id")),
        "info": {"music": {
            "title": item.name,
            "count": item.song_count,
            "duration": item.duration,
            "date": item.created,
        }},
    }


def artist_entry(conn, item, params):
    image = art_path(conn, item.cover_art)
    return {
        "label": starred_label(item.id, item.name),
        "thumb": image,
        "fanart": image,
        "url": url_for("list_albums", artist_id=item.id, menu_id=params.get("menu_id")),
        "info": {"music": {
            "artist": item.name,
            "count": _get(item, "album_count"),
        }},
        "context_menu": _context_menu("artist", item.id),
    }


def album_entry(conn, item, params):
    image = art_path(conn, item.cover_art)
    return {
        "label": album_label(item, params.get("hide_artist", False)),
        "thumb": image,
        "fanart": image,
        "url": url_for("list_tracks", album_id=item.id,
                       hide_artist=params.get("hide_artist"),
                       menu_id=params.get("menu_id")),
        "info": {"music": {
            "count": _get(item, "song_count"),
            "date": item.created,
            "duration": _get(item, "duration"),
            "artist": _get(item, "artist"),
            "album": _album_name(item),
            "year": _get(item, "year"),
        }},
        "context_menu": _context_menu("album", item.id),
    }


def track_entry(conn, item, params):
    image = art_path(conn, item.cover_art)
    return {
        "label": track_label(item, params.get("hide_artist")),
        "thumb": image,
        "fanart": image,
        "url": url_for("play_track", id=item.id, menu_id=params.get("menu_id")),
        "is_playable": True,
        "mime": item.content_type,
        "info": {"music": {
            "title": item.title,
            "album": item.album,
            "artist": item.artist,
            "tracknumber": item.track,
            "year": item.year,
            "genre": item.genre,
            "size": item.size,
            "duration": item.duration,
            "date": item.created,
        }},
        "context_menu": _context_menu("track", item.id),
    }
