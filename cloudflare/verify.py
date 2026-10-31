"""Compare the running local Wrangler API with Python on an in-memory DB only."""
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from planner import calculate_plan, set_inventory
base = "http://127.0.0.1:8787"
def get(path):
    with urlopen(base+path,timeout=20) as res:
        return json.load(res)
def comparable(p):
    return {k:v for k,v in p.items() if k != "notes"}
def main():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.executescript((ROOT/"cloudflare/migrations/0001_standard_data.sql").read_text(encoding="utf-8"))
    assert get('/api/stats') == dict(characters=120,materials=309,ascension_rows=3480,talent_rows=3840,revision='49a6544a6c')
    chars=get('/api/characters')
    assert len(chars)==120
    fixtures=[]
    cases=[(0,6,[(1,1)]*3),(0,6,[(1,10)]*3),(2,5,[(2,4),(3,8),(1,6)]),(4,4,[(6,6)]*3)]
    for c in chars:
        for a,b,values in cases:
            talents=dict(zip(['attack','skill','burst'],values))
            args={'character_id':c['id'],'from_phase':a,'to_phase':b}
            for k,(x,y) in talents.items():args.update({k+'_from':x,k+'_to':y})
            cloud=get('/api/plan?'+urlencode(args))
            expected=calculate_plan(db,c['id'],a,b,talents)
            assert comparable(cloud)==json.loads(json.dumps(comparable(expected),ensure_ascii=False)), c['id']
            stocks={}
            for i,m in enumerate(cloud['materials']):
                q=[0,m['required']//2,m['required'],m['required']+10][i%4]
                stocks[str(m['id'])]=q
                set_inventory(db,m['id'],q)
            expected=calculate_plan(db,c['id'],a,b,talents)
            fixtures.append({'cloud':cloud,'stocks':stocks,'expected':comparable(expected)})
            db.execute('DELETE FROM inventory')
    js="""import {withInventory} from './plan.js';import assert from 'node:assert/strict';let raw='';for await(const c of process.stdin)raw+=c;for(const f of JSON.parse(raw)){const p=withInventory(f.cloud,f.stocks);delete p.notes;assert.deepEqual(p,f.expected);}console.log('Browser inventory parity: '+JSON.parse(raw).length);"""
    subprocess.run(['node','--input-type=module','-e',js],input=json.dumps(fixtures),text=True,cwd=ROOT/'cloudflare',check=True)
    for path in ['/api/plan?to_phase=7','/api/plan?character_id=999','/api/plan?attack_to=1.5']:
        try:get(path);raise AssertionError(path)
        except HTTPError as e:assert e.code==400
    for method in ['POST','PUT','DELETE']:
        try:
            urlopen(Request(base+'/api/inventory',data=b'{}',method=method));raise AssertionError(method)
        except HTTPError as e:assert e.code==405
    for path in ['/','/app.js','/style.css','/images/characters/placeholder.svg']:
        with urlopen(base+path) as res:assert res.status==200
    assert get('/images/characters/manifest.json')=={'characters':{}}
    try:urlopen(base+'/images/characters/10000023.webp');raise AssertionError('game image exposed')
    except HTTPError as e:assert e.code==404
    print(f'Worker/Python zero-stock parity: {len(fixtures)}; all routes and read-only restrictions passed')
if __name__=='__main__':main()
