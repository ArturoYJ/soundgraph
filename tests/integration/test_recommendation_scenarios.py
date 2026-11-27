"""Escenarios sintéticos de la consulta real de Neo4j; cada caso revierte su transacción.

Ejecutar solo con SOUNDGRAPH_ISOLATED_TEST=1 y una base aislada. Los esperados
son explícitos, no se derivan de la consulta bajo prueba. No mide relevancia musical.
"""
import os
import pytest
from scripts.storage import DATABASE_DIR, create_graph_driver

pytestmark = pytest.mark.skipif(os.getenv('SOUNDGRAPH_ISOLATED_TEST') != '1', reason='Requiere Neo4j aislado')

# (nombre, relaciones perfil-canción, perfil consultado, límite, salida esperada)
CASES = [
 ('perfil_inexistente', [('v','a')], 'missing', 10, []),
 ('sin_historial', [('v','a')], 'me', 10, []),
 ('sin_vecino_compartido', [('me','a'),('v','b')], 'me', 10, []),
 ('coincidencia_sin_candidatas', [('me','a'),('v','a')], 'me', 10, []),
 ('una_candidata', [('me','a'),('v','a'),('v','x')], 'me', 10, [('x',1)]),
 ('dos_compartidas_un_perfil', [('me','a'),('me','b'),('v','a'),('v','b'),('v','x')], 'me', 10, [('x',1)]),
 ('dos_perfiles_una_candidata', [('me','a'),('v','a'),('v','x'),('w','a'),('w','x')], 'me', 10, [('x',2)]),
 ('excluye_escuchada', [('me','a'),('me','x'),('v','a'),('v','x'),('v','y')], 'me', 10, [('y',1)]),
 ('ordena_afinidad_y_desempate', [('me','a'),('v','a'),('v','x'),('v','y'),('v','z'),('w','a'),('w','z')], 'me', 10, [('z',2),('x',1),('y',1)]),
 ('respeta_limite', [('me','a'),('v','a'),('v','x'),('v','y'),('v','z'),('w','a'),('w','z')], 'me', 2, [('z',2),('x',1)]),
 ('ignora_perfil_sin_coincidencia', [('me','a'),('v','a'),('v','x'),('w','b'),('w','x')], 'me', 10, [('x',1)]),
 ('vecino_escucha_multiples_nuevas', [('me','a'),('v','a'),('v','x'),('v','y')], 'me', 10, [('x',1),('y',1)]),
]

@pytest.mark.parametrize('name,edges,subject,limit,expected', CASES, ids=[case[0] for case in CASES])
def test_synthetic_graph(name, edges, subject, limit, expected):
    prefix = 'cartel_eval_' + name + '_'
    query = (DATABASE_DIR / 'neo4j/queries/recommendations.cypher').read_text(encoding='utf-8')
    profiles = sorted({p for p, _ in edges} | ({subject} if subject != 'missing' else set()))
    songs = sorted({s for _, s in edges})
    with create_graph_driver() as driver, driver.session(database='neo4j') as session:
        tx = session.begin_transaction()
        try:
            tx.run('UNWIND $ids AS id CREATE (:Perfil {profileId: id})', ids=[prefix+p for p in profiles]).consume()
            tx.run('UNWIND $ids AS id CREATE (:Cancion {songId: id})', ids=[prefix+s for s in songs]).consume()
            tx.run('UNWIND $edges AS e MATCH (p:Perfil {profileId:e.p}), (s:Cancion {songId:e.s}) CREATE (p)-[:`ESCUCHÓ`]->(s)', edges=[{'p':prefix+p,'s':prefix+s} for p,s in edges]).consume()
            rows = list(tx.run(query, profile_id=prefix+subject, limit=limit))
            actual = [(r['song_id'].removeprefix(prefix), r['affinity']) for r in rows]
            assert actual == expected
        finally:
            tx.rollback()
