"""24 escenarios aislados por API real, grafo y catálogo; restaura la semilla al finalizar."""
import http.cookiejar, json, os, urllib.request
from scripts import evaluate_graph_volume as volume
from scripts.storage import open_stores

if os.getenv('SOUNDGRAPH_ISOLATED_TEST') != '1': raise SystemExit('Usar solo en entorno aislado')
PREFIX='evalapi-'
headers={'Origin':'http://127.0.0.1:18136','Host':'127.0.0.1:18136','Content-Type':'application/json'}
base='http://api:8000/api/v1'
codes=dict(line.strip().split('=',1) for line in open('/tmp/soundgraph-codes') if line.strip() and not line.startswith('#'))
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(path, method='GET', data=None):
    req=urllib.request.Request(base+path, data=json.dumps(data).encode() if data is not None else None, headers=headers, method=method)
    with client.open(req,timeout=15) as resp: return resp.status,json.loads(resp.read()) if resp.status!=204 else None

def main():
    count=ok=partials=0
    with open_stores() as stores:
        g=stores.graph; mongo=stores.mongo.songs
        # Se modifica solo la copia de datos del proyecto Compose aislado.
        old,_,_=g.execute_query('MATCH (:Perfil {profileId:$id})-[:`ESCUCHÓ`]->(s:Cancion) RETURN s.songId AS id',id='p-ana-main',database_='neo4j')
        prior=[r['id'] for r in old]
        try:
            g.execute_query('MATCH (:Perfil {profileId:$id})-[r:`ESCUCHÓ`]->(:Cancion) DELETE r',id='p-ana-main',database_='neo4j')
            status,_=request('/demo/sessions','POST',{'profileId':'p-ana-main','code':codes['DEMO_CODE_ANA']}); assert status==201
            for category in volume.CATEGORIES:
                for i in range(4):
                    edges=sorted(volume.case(category)); limit=10; expected=volume.oracle(edges,limit)
                    prefix=PREFIX+category.replace('_','-')+'-'+str(i)+'-'
                    people=sorted({p for p,_ in edges if p!='me'}); songs=sorted({s for _,s in edges})
                    ids=[prefix+s for s in songs]
                    missing=expected[-1][0] if expected and i%2 else None
                    try:
                        g.execute_query('UNWIND $ids AS id CREATE (:Perfil:EvalApi {profileId:id})',ids=[prefix+p for p in people],database_='neo4j')
                        g.execute_query('UNWIND $ids AS id CREATE (:Cancion:EvalApi {songId:id})',ids=ids,database_='neo4j')
                        g.execute_query('UNWIND $rows AS e MATCH (p:Perfil {profileId:e.p}), (s:Cancion {songId:e.s}) CREATE (p)-[:`ESCUCHÓ`]->(s)',rows=[{'p':('p-ana-main' if p=='me' else prefix+p),'s':prefix+s} for p,s in edges],database_='neo4j')
                        docs=[{'_id':prefix+s,'title':'Pista de prueba '+s,'editorial':{'credits':[{'name':'Prueba','role':'artista'}]}} for s in songs if s!=missing]
                        if docs: mongo.insert_many(docs)
                        status,body=request('/recommendations?limit=10')
                        actual=[(x['song']['songId'].removeprefix(prefix),x['affinity']) for x in body['items']]
                        wanted=[x for x in expected if x[0]!=missing]
                        matched=status==200 and body['partial']==bool(missing) and actual==wanted
                        count+=1;ok+=matched;partials+=bool(missing)
                        print(json.dumps({'category':category,'index':i,'edges':edges,'missing':missing,'expected':wanted,'actual':actual,'partial':body['partial'],'status':status,'ok':matched},ensure_ascii=False),flush=True)
                    finally:
                        mongo.delete_many({'_id':{'$in':ids}})
                        g.execute_query('MATCH (n:EvalApi) DETACH DELETE n',database_='neo4j')
            request('/demo/sessions/current','DELETE')
        finally:
            mongo.delete_many({'_id':{'$regex':'^evalapi-'}})
            g.execute_query('MATCH (n:EvalApi) DETACH DELETE n',database_='neo4j')
            g.execute_query('UNWIND $ids AS id MATCH (p:Perfil {profileId:$profile}), (s:Cancion {songId:id}) MERGE (p)-[:`ESCUCHÓ`]->(s)',ids=prior,profile='p-ana-main',database_='neo4j')
    print(json.dumps({'type':'summary','total':count,'correct':ok,'partial_cases':partials}),flush=True)
    if ok!=count: raise SystemExit(1)
if __name__=='__main__':main()
