"""600 graphs sintéticos: consulta real Neo4j frente a un oráculo Python independiente.
Solo entorno aislado. Cada caso se revierte y se emite como JSONL para auditoría.
"""
import json
import os
import random
from collections import Counter, defaultdict
from scripts.storage import DATABASE_DIR, create_graph_driver

if os.getenv('SOUNDGRAPH_ISOLATED_TEST') != '1':
    raise SystemExit('SOUNDGRAPH_ISOLATED_TEST=1 requerido; usar solo una base aislada')

SEED = 20261126
rng = random.Random(SEED)
CATEGORIES = ('sin_historial', 'sin_vecino', 'sin_candidatas', 'vecino_unico', 'varios_vecinos', 'mixto')
QUERY = (DATABASE_DIR / 'neo4j/queries/recommendations.cypher').read_text(encoding='utf-8')

def oracle(edges, limit):
    listens = defaultdict(set)
    for person, song in edges:
        listens[person].add(song)
    mine = listens['me']
    counts = Counter()
    for person, heard in listens.items():
        if person != 'me' and mine & heard:
            for song in heard - mine:
                counts[song] += 1
    return sorted(counts.items(), key=lambda row: (-row[1], row[0]))[:limit]

def case(category):
    songs = ['s%02d' % i for i in rng.sample(range(100), 12)]
    people = ['v%02d' % i for i in rng.sample(range(100), 6)]
    a,b,c,d = songs[:4]; v,w = people[:2]
    if category == 'sin_historial':
        return {(p,s) for p in people for s in rng.sample(songs, rng.randrange(1,5))}
    if category == 'sin_vecino':
        return {('me',a), ('me',b)} | {(p,s) for p in people for s in rng.sample(songs[2:], rng.randrange(1,5))}
    if category == 'sin_candidatas':
        return {('me',s) for s in songs[:4]} | {(p,s) for p in people for s in rng.sample(songs[:4], rng.randrange(1,5))}
    if category == 'vecino_unico':
        return {('me',a), ('me',b), (v,a), (v,b), (v,c), (v,d)} | {(p,s) for p in people[1:] for s in rng.sample(songs[4:], rng.randrange(1,4))}
    if category == 'varios_vecinos':
        return {('me',a),('me',b),(v,a),(v,c),(w,b),(w,c),(w,d)}
    return {(p,s) for p in ['me']+people for s in rng.sample(songs, rng.randrange(0,8))}

def run():
    summary=Counter(); returned=0; incorrect=0; actual_heard=0
    with create_graph_driver() as driver, driver.session(database='neo4j') as session:
        for category in CATEGORIES:
            for index in range(100):
                edges=sorted(case(category)); limit=rng.choice([1,2,3,5,10]); expected=oracle(edges,limit)
                prefix='vol-%s-%03d-' % (category.replace('_','-'),index)
                persons=sorted({p for p,_ in edges}|{'me'}); songs=sorted({s for _,s in edges})
                tx=session.begin_transaction()
                try:
                    tx.run('UNWIND $ids AS id CREATE (:Perfil {profileId:id})',ids=[prefix+p for p in persons]).consume()
                    tx.run('UNWIND $ids AS id CREATE (:Cancion {songId:id})',ids=[prefix+s for s in songs]).consume()
                    tx.run('UNWIND $rows AS e MATCH (p:Perfil {profileId:e.p}), (s:Cancion {songId:e.s}) CREATE (p)-[:`ESCUCHÓ`]->(s)',rows=[{'p':prefix+p,'s':prefix+s} for p,s in edges]).consume()
                    actual=[(r['song_id'].removeprefix(prefix),r['affinity']) for r in tx.run(QUERY,profile_id=prefix+'me',limit=limit)]
                finally:
                    tx.rollback()
                ok=actual==expected; summary[category+'_total']+=1; summary[category+'_ok']+=int(ok)
                returned+=len(actual); actual_heard+=sum(('me',s) in edges for s,_ in actual); incorrect+=not ok
                print(json.dumps({'type':'case','category':category,'index':index,'limit':limit,'edges':edges,'expected':expected,'actual':actual,'ok':ok},ensure_ascii=False),flush=True)
    print(json.dumps({'type':'summary','seed':SEED,'total':sum(summary[c+'_total'] for c in CATEGORIES),'correct':sum(summary[c+'_ok'] for c in CATEGORIES),'failed':incorrect,'returned':returned,'already_heard_returned':actual_heard,'categories':dict(summary)},ensure_ascii=False),flush=True)
    if incorrect: raise SystemExit(1)

if __name__=='__main__': run()
