MATCH (me:Perfil {profileId: $profile_id})-[:`ESCUCHÓ`]->(shared:Cancion)
      <-[:`ESCUCHÓ`]-(similar:Perfil)-[:`ESCUCHÓ`]->(candidate:Cancion)
WHERE me <> similar
  AND candidate.songId IS NOT NULL
  AND NOT EXISTS { MATCH (me)-[:`ESCUCHÓ`]->(candidate) }
WITH candidate.songId AS song_id, count(DISTINCT similar) AS affinity
RETURN song_id, affinity
ORDER BY affinity DESC, song_id ASC
LIMIT $limit
