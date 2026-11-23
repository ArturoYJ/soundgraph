UNWIND $ids AS id
MERGE (:Cancion {songId: id})
