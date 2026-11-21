CREATE TABLE IF NOT EXISTS profiles (
    profile_id text PRIMARY KEY CHECK (profile_id ~ '^[a-zA-Z0-9][a-zA-Z0-9-]{0,63}$'),
    display_name text NOT NULL CHECK (length(btrim(display_name)) BETWEEN 1 AND 100),
    role text NOT NULL CHECK (role IN ('listener', 'editor'))
);

CREATE TABLE IF NOT EXISTS playlists (
    playlist_id text PRIMARY KEY CHECK (playlist_id ~ '^[a-zA-Z0-9][a-zA-Z0-9-]{0,63}$'),
    owner_id text NOT NULL REFERENCES profiles(profile_id),
    name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS playlists_owner_idx ON playlists(owner_id);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    playlist_id text NOT NULL REFERENCES playlists(playlist_id) ON DELETE CASCADE,
    song_id text NOT NULL CHECK (song_id ~ '^[a-zA-Z0-9][a-zA-Z0-9-]{0,63}$'),
    position integer NOT NULL CHECK (position > 0),
    PRIMARY KEY (playlist_id, song_id),
    CONSTRAINT playlist_position_unique UNIQUE (playlist_id, position) DEFERRABLE
);
