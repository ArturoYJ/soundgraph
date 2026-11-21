import logging

from backend.errors import missing_song
from backend.schemas import PlaylistDetail, Recommendation, Recommendations, SavedTrack, Track

log = logging.getLogger("soundgraph.discovery")


def discover(profile, graph, catalog, limit):
    candidates = graph.recommendations(profile.profileId, limit)
    songs = catalog.by_ids([song_id for song_id, _ in candidates])
    missing = [song_id for song_id, _ in candidates if song_id not in songs]
    if missing:
        log.warning("recommendation_missing_fiches song_ids=%s", ",".join(missing))
    return Recommendations(
        items=[Recommendation(song=songs[song_id], affinity=affinity)
               for song_id, affinity in candidates if song_id in songs],
        partial=bool(missing),
    )


def playlist_detail(profile, sql, catalog, playlist_id):
    name, rows = sql.detail(profile.profileId, playlist_id)
    songs = catalog.by_ids([song_id for song_id, _ in rows]) if rows else {}
    return PlaylistDetail(
        playlistId=playlist_id, name=name, trackCount=len(rows),
        tracks=[Track(songId=song_id, position=position, song=songs.get(song_id))
                for song_id, position in rows],
    )


def save_track(profile, sql, catalog, playlist_id, song_id):
    sql.owned_playlist(profile.profileId, playlist_id)
    if not catalog.exists(song_id):
        raise missing_song()
    position, created = sql.save_track(profile.profileId, playlist_id, song_id)
    return SavedTrack(playlistId=playlist_id, songId=song_id, position=position, created=created)
