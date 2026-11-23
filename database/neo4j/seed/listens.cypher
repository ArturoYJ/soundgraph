UNWIND $rows AS row
MATCH (p:Perfil {profileId: row.profileId}), (s:Cancion {songId: row.songId})
MERGE (p)-[:`ESCUCHÓ`]->(s)
