CREATE CONSTRAINT profile_id_unique IF NOT EXISTS
FOR (profile:Perfil) REQUIRE profile.profileId IS UNIQUE;

CREATE CONSTRAINT song_id_unique IF NOT EXISTS
FOR (song:Cancion) REQUIRE song.songId IS UNIQUE;
