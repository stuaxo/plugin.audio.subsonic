"""Generators that walk the OpenSubsonic API responses.

libopensonic returns typed dataclasses rather than raw dicts, so these walk
the object graph directly instead of chained ``.get(...)`` lookups.
"""


def walk_folders(conn):
    yield from conn.get_music_folders()


def walk_index(conn, folder_id=None):
    for index in conn.get_indexes(folder_id).index or []:
        yield from index.artist or []


def walk_directory(conn, directory_id, merge_artist=True):
    for child in conn.get_music_directory(directory_id).child or []:
        if merge_artist and child.is_dir:
            yield from walk_directory(conn, child.id, merge_artist)
        else:
            yield child


def walk_artists(conn):
    for index in conn.get_artists().index or []:
        yield from index.artist or []


def walk_artist(conn, artist_id):
    yield from conn.get_artist(artist_id).album or []


def walk_albums(conn, ltype, size=None, from_year=None, to_year=None, genre=None, offset=None):
    if ltype == "byGenre" and genre is None:
        return
    if ltype == "byYear" and (from_year is None or to_year is None):
        return
    yield from conn.get_album_list2(
        ltype=ltype, size=size, from_year=from_year, to_year=to_year, genre=genre, offset=offset
    )


def walk_album(conn, album_id):
    yield from conn.get_album(album_id).song or []


def walk_playlists(conn):
    yield from conn.get_playlists()


def walk_playlist(conn, playlist_id):
    yield from conn.get_playlist(playlist_id).entry or []


def walk_tracks_random(conn, size=None, genre=None, from_year=None, to_year=None):
    yield from conn.get_random_songs(size=size, genre=genre, from_year=from_year, to_year=to_year)


def walk_tracks_starred(conn):
    yield from conn.get_starred().song or []


def walk_genres(conn):
    yield from conn.get_genres()
