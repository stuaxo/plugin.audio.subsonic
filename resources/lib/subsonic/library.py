"""Generators that walk the Subsonic API responses."""


def walk_folders(conn):
    response = conn.getMusicFolders()
    yield from (response.get("musicFolders") or {}).get("musicFolder") or []


def walk_index(conn, folder_id=None):
    response = conn.getIndexes(folder_id)
    for index in (response.get("indexes") or {}).get("index") or []:
        yield from index.get("artist") or []


def walk_directory(conn, directory_id, merge_artist=True):
    response = conn.getMusicDirectory(directory_id)
    for child in (response.get("directory") or {}).get("child") or []:
        if merge_artist and child.get("isDir"):
            yield from walk_directory(conn, child["id"], merge_artist)
        else:
            yield child


def walk_artists(conn):
    response = conn.getArtists()
    for index in (response.get("artists") or {}).get("index") or []:
        yield from index.get("artist") or []


def walk_artist(conn, artist_id):
    response = conn.getArtist(artist_id)
    yield from (response.get("artist") or {}).get("album") or []


def walk_albums(conn, ltype, size=None, fromYear=None, toYear=None, genre=None, offset=None):
    if ltype == "byGenre" and genre is None:
        return
    if ltype == "byYear" and (fromYear is None or toYear is None):
        return
    response = conn.getAlbumList2(
        ltype=ltype, size=size, fromYear=fromYear, toYear=toYear, genre=genre, offset=offset
    )
    yield from (response.get("albumList2") or {}).get("album") or []


def walk_album(conn, album_id):
    response = conn.getAlbum(album_id)
    yield from (response.get("album") or {}).get("song") or []


def walk_playlists(conn):
    response = conn.getPlaylists()
    yield from (response.get("playlists") or {}).get("playlist") or []


def walk_playlist(conn, playlist_id):
    response = conn.getPlaylist(playlist_id)
    yield from (response.get("playlist") or {}).get("entry") or []


def walk_tracks_random(conn, size=None, genre=None, fromYear=None, toYear=None):
    response = conn.getRandomSongs(size=size, genre=genre, fromYear=fromYear, toYear=toYear)
    yield from (response.get("randomSongs") or {}).get("song") or []


def walk_tracks_starred(conn):
    response = conn.getStarred()
    yield from (response.get("starred") or {}).get("song") or []


def walk_genres(conn):
    response = conn.getGenres()
    yield from (response.get("genres") or {}).get("genre") or []
