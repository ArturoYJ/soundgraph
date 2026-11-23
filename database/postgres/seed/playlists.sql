INSERT INTO playlists VALUES (%s, %s, %s)
ON CONFLICT (playlist_id) DO NOTHING;
