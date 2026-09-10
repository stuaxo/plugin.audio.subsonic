"""Plugin actions (directory listings + playback resolution)."""

import json

import xbmcgui

from . import addon, cache, client, downloads, entries, library
from .listing import add_directory_items, create_listing, set_resolved_url
from .router import action, url_for


def _json_param(params, key):
    try:
        return json.loads(params[key])
    except (KeyError, ValueError):
        return {}


def _navigate_root():
    return {"label": addon.L(30030), "url": url_for("root")}


def _navigate_next(params):
    page = int(params.get("page", 1)) + 1
    return {
        "label": "%s(%d)" % (addon.L(30029), page),
        "url": url_for(
            params.get("action", "root"),
            page=page,
            query_args=params.get("query_args"),
        ),
    }


# --- top-level menus -------------------------------------------------------

@action()
def root(params):
    if client.get_connection() is None:
        return

    menu = [
        (addon.L(30038), "browse_folders", "folders"),
        (addon.L(30019), "browse_library", "library"),
        (addon.L(30020), "menu_albums", "albums"),
        (addon.L(30021), "menu_tracks", "tracks"),
        (addon.L(30022), "list_playlists", "playlists"),
        (addon.L(30039), "search", "search"),
        (addon.L(30045), "search_album", "searchalbum"),
    ]
    listing = [
        {"label": label, "url": url_for(callback, menu_id=menu_id)}
        for label, callback, menu_id in menu
    ]
    add_directory_items(create_listing(listing))


@action()
def menu_albums(params):
    if client.get_connection() is None:
        return

    menu = [
        (addon.L(30023), "newest"),
        (addon.L(30024), "frequent"),
        (addon.L(30025), "recent"),
        (addon.L(30026), "random"),
    ]
    listing = [
        {
            "label": label,
            "url": url_for("list_albums", page=1,
                           query_args=json.dumps({"ltype": ltype}),
                           menu_id="albums_%s" % ltype),
        }
        for label, ltype in menu
    ]
    add_directory_items(create_listing(listing))


@action()
def menu_tracks(params):
    if client.get_connection() is None:
        return

    menu = [(addon.L(30036), "tracks_starred"), (addon.L(30037), "tracks_random")]
    listing = [
        {"label": label, "url": url_for("list_tracks", menu_id=menu_id)}
        for label, menu_id in menu
    ]
    add_directory_items(create_listing(listing))


# --- folder browsing (directory structure) -------------------------------

@action()
def browse_folders(params):
    conn = client.get_connection()
    if conn is None:
        return

    listing = [
        {
            "label": item.get("name"),
            "url": url_for("browse_indexes", folder_id=item.get("id"),
                           menu_id=params.get("menu_id")),
        }
        for item in library.walk_folders(conn)
    ]
    if len(listing) == 1:
        return browse_indexes(params)
    add_directory_items(create_listing(listing))


@action()
def browse_indexes(params):
    conn = client.get_connection()
    if conn is None:
        return

    listing = [
        {
            "label": item.get("name"),
            "url": url_for("list_directory", id=item.get("id"),
                           menu_id=params.get("menu_id")),
        }
        for item in library.walk_index(conn, params.get("folder_id"))
    ]
    add_directory_items(create_listing(listing))


@action()
def list_directory(params):
    conn = client.get_connection()
    if conn is None:
        return

    merge = addon.setting_bool("merge")
    listing = []
    for item in library.walk_directory(conn, params.get("id"), merge):
        if item.get("isDir"):
            listing.append({
                "label": item.get("title"),
                "url": url_for("list_directory", id=item.get("id"),
                               menu_id=params.get("menu_id")),
            })
        else:
            listing.append(entries.track_entry(conn, item, params))
    add_directory_items(create_listing(listing))


# --- library browsing (ID3 tags) ----------------------------------------

@action()
def browse_library(params):
    conn = client.get_connection()
    if conn is None:
        return

    listing = [entries.artist_entry(conn, item, params) for item in library.walk_artists(conn)]
    add_directory_items(create_listing(listing, cache_to_disk=True, content="artists"))


@action()
def list_albums(params):
    conn = client.get_connection()
    if conn is None:
        return

    per_page = addon.setting_int("albums_per_page", 50)
    query_args = _json_param(params, "query_args")
    query_args["size"] = per_page
    page = int(params.get("page", 1))
    if page > 1:
        query_args["offset"] = (page - 1) * per_page

    if "artist_id" in params:
        items = list(library.walk_artist(conn, params["artist_id"]))
    else:
        items = list(library.walk_albums(conn, **query_args))

    if len(items) <= 1:
        params["hide_artist"] = True

    listing = [entries.album_entry(conn, item, params) for item in items]
    listing.append(_navigate_root())
    if "artist_id" not in params:
        listing.append(_navigate_next(params))

    add_directory_items(create_listing(listing, cache_to_disk=True, content="albums"))


@action()
def list_tracks(params):
    conn = client.get_connection()
    if conn is None:
        return

    menu_id = params.get("menu_id")
    per_page = addon.setting_int("tracks_per_page", 100)
    query_args = _json_param(params, "query_args")
    query_args["size"] = per_page
    page = int(params.get("page", 1))
    if page > 1:
        query_args["offset"] = (page - 1) * per_page

    if "album_id" in params:
        items = list(library.walk_album(conn, params["album_id"]))
    elif "playlist_id" in params:
        items = list(library.walk_playlist(conn, params["playlist_id"]))
    elif menu_id == "tracks_starred":
        items = list(library.walk_tracks_starred(conn))
        cache.refresh(forced=True)
    elif menu_id == "tracks_random":
        items = list(library.walk_tracks_random(conn, **query_args))
    else:
        items = []

    if len(items) <= 1:
        params["hide_artist"] = True

    listing = [entries.track_entry(conn, item, params) for item in items]
    add_directory_items(create_listing(listing, content="songs"))


@action()
def list_playlists(params):
    conn = client.get_connection()
    if conn is None:
        return

    listing = [entries.playlist_entry(conn, item, params) for item in library.walk_playlists(conn)]
    add_directory_items(create_listing(listing))


# --- search --------------------------------------------------------------

@action()
def search(params):
    query = xbmcgui.Dialog().input(addon.L(30039))

    listing = []
    if query:
        conn = client.get_connection()
        if conn is None:
            return
        songs = (conn.search2(query=query).get("searchResult2") or {}).get("song")
        if songs:
            listing = [entries.track_entry(conn, song, params) for song in songs]

    if not listing:
        return browse_indexes(params)
    add_directory_items(create_listing(listing))


@action()
def search_album(params):
    query = xbmcgui.Dialog().input(addon.L(30045))

    listing = []
    if query:
        conn = client.get_connection()
        if conn is None:
            return
        result = conn.search2(query=query, artistCount=0, songCount=0)
        albums = (result.get("searchResult2") or {}).get("album")
        if albums:
            listing = [entries.album_entry(conn, album, params) for album in albums]

    if not listing:
        return browse_indexes(params)
    add_directory_items(create_listing(listing))


# --- playback + actions -------------------------------------------------

@action()
def play_track(params):
    conn = client.get_connection()
    if conn is None:
        return

    url = conn.streamUrl(
        sid=params["id"],
        maxBitRate=addon.setting("bitrate_streaming"),
        tformat=addon.setting("transcode_format_streaming"),
        estimateContentLength=True,
    )
    set_resolved_url(url)


@action()
def star_item(params):
    item_type = params.get("type")
    ids = params.get("ids")
    unstar = str(params.get("unstar")).lower() in ("true", "1")

    if not entries.can_star(item_type, ids):
        return

    conn = client.get_connection()
    if conn is None:
        return

    sids = ids if item_type == "track" else None
    album_ids = ids if item_type == "album" else None
    artist_ids = ids if item_type == "artist" else None

    try:
        response = (conn.unstar if unstar else conn.star)(sids, album_ids, artist_ids)
        ok = response.get("status") == "ok"
    except Exception as exc:  # noqa: BLE001
        addon.log_error("star_item failed: %r" % exc)
        ok = False

    if ok:
        cache.refresh(forced=True)
        addon.notify(addon.L(30031) if unstar else addon.L(30032))
    else:
        addon.log_error("Unable to %s %s %s" % ("unstar" if unstar else "star", item_type, ids))


@action()
def download_item(params):
    downloads.download_item(params)
