"""Comparación local secuencial con tres semillas sintéticas y salida JSONL."""
import http.cookiejar, json, math, os, random, statistics, time, urllib.request
from scripts.storage import open_stores
from scripts.evaluate_graph_volume import oracle
if os.getenv('SOUNDGRAPH_ISOLATED_TEST')!='1': raise SystemExit('Requiere entorno aislado')
headers={'Origin':'http://127.0.0.1:18136','Host':'127.0.0.1:18136','Content-Type':'application/json'}
base='http://api:8000/api/v1'
codes=dict(l.strip().split('=',1) for l in open('/tmp/soundgraph-codes') if l.strip() and not l.startswith('#'))
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def req(path,method='GET',data=None):
    request=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method)
    start=time.perf_counter_ns()
    with client.open(request,timeout=30) as r: status=r.status; raw=r.read()
    return status,(json.loads(raw) if raw else None),(time.perf_counter_ns()-start)/1e6

def main():
    scales=[(10,50,200),(100,500,5000),(500,2000,25000)]
    with open_stores() as stores:
        g=stores.graph; mongo=stores.mongo.songs; pg=stores.postgres
        original,_,_=g.execute_query('MATCH (:Perfil {profileId:$id})-[:`ESCUCHÓ`]->(s:Cancion) RETURN s.songId AS id',id='p-ana-main',database_='neo4j')
        prior=[r['id'] for r in original]
        try:
            g.execute_query('MATCH (:Perfil {profileId:$id})-[r:`ESCUCHÓ`]->(:Cancion) DELETE r',id='p-ana-main',database_='neo4j')
            assert req('/demo/sessions','POST',{'profileId':'p-ana-main','code':codes['DEMO_CODE_ANA']})[0]==201
            for profiles,songs,nedges in scales:
                rng=random.Random(20261126+profiles)
                ps=['p-ana-main']+['scale-p-%04d'%i for i in range(profiles-1)]
                ss=['scale-s-%04d'%i for i in range(songs)]
                chosen=rng.sample(range(profiles*songs),nedges)
                edges=[(ps[x//songs],ss[x%songs]) for x in chosen]
                expected=oracle([('me' if p=='p-ana-main' else p,s) for p,s in edges],10)
                try:
                    with pg.cursor() as cur: cur.executemany('INSERT INTO profiles (profile_id,display_name,role) VALUES (%s,%s,%s)',[(p,'Perfil sintético','listener') for p in ps[1:]])
                    mongo.insert_many([{'_id':s,'title':'Pista sintética '+s,'editorial':{'credits':[{'name':'Prueba','role':'artista'}]}} for s in ss])
                    g.execute_query('UNWIND $ids AS id CREATE (:Perfil:EvalScale {profileId:id})',ids=ps[1:],database_='neo4j')
                    g.execute_query('UNWIND $ids AS id CREATE (:Cancion:EvalScale {songId:id})',ids=ss,database_='neo4j')
                    for start in range(0,len(edges),5000):
                        g.execute_query('UNWIND $rows AS e MATCH (p:Perfil {profileId:e.p}), (s:Cancion {songId:e.s}) CREATE (p)-[:`ESCUCHÓ`]->(s)',rows=[{'p':p,'s':s} for p,s in edges[start:start+5000]],database_='neo4j')
                    times=[]
                    for i in range(310):
                        status,body,ms=req('/recommendations?limit=10')
                        got=[(r['song']['songId'],r['affinity']) for r in body['items']]
                        if status!=200 or body['partial'] or got!=expected: raise AssertionError((profiles,i,status,got,expected))
                        if i>=10:
                            times.append(ms)
                            print(json.dumps({'type':'sample','profiles':profiles,'songs':songs,'listens':nedges,'round':(i-10)//100+1,'sample':(i-10)%100+1,'ms':round(ms,6),'status':status}),flush=True)
                    for rnd in range(3):
                        values=sorted(times[rnd*100:(rnd+1)*100])
                        print(json.dumps({'type':'round','profiles':profiles,'songs':songs,'listens':nedges,'round':rnd+1,'n':len(values),'median_ms':round(statistics.median(values),3),'p95_ms':round(values[94],3),'max_ms':round(max(values),3),'candidates':len(expected)}),flush=True)
                finally:
                    g.execute_query('MATCH (n:EvalScale) DETACH DELETE n',database_='neo4j')
                    mongo.delete_many({'_id':{'$in':ss}})
                    pg.execute('DELETE FROM profiles WHERE profile_id = ANY(%s)',(ps[1:],))
            req('/demo/sessions/current','DELETE')
        finally:
            g.execute_query('MATCH (n:EvalScale) DETACH DELETE n',database_='neo4j')
            g.execute_query('UNWIND $ids AS id MATCH (p:Perfil {profileId:$profile}), (s:Cancion {songId:id}) MERGE (p)-[:`ESCUCHÓ`]->(s)',ids=prior,profile='p-ana-main',database_='neo4j')
if __name__=='__main__':main()
