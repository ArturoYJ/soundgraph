UNWIND $ids AS id
MERGE (:Perfil {profileId: id})
