import test from 'node:test';
import assert from 'node:assert/strict';
import {cloudApi} from './inventory.js';
import {selection} from './worker.js';
const fake = () => {const map=new Map();return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,v)}};
const plan={materials:[{id:1,required:10,category:'其他',name_zh:'甲',owned:0,missing:10}],shortage_count:1};
test('browser inventory: zero, persistence, isolation, shortage',async()=>{
 const store=fake(), network=async()=>structuredClone(plan), api=cloudApi(network,()=>store);
 const save=q=>api('/api/inventory',{body:JSON.stringify({material_id:1,quantity:q})});
 await save(4);assert.equal((await api('/api/plan?')).materials[0].missing,6);
 assert.equal((await cloudApi(network,()=>store)('/api/plan?')).materials[0].owned,4);
 assert.equal((await cloudApi(network,()=>fake())('/api/plan?')).materials[0].owned,0);
 await save(0);assert.equal((await api('/api/plan?')).materials[0].missing,10);
 await save(20);assert.equal((await api('/api/plan?')).shortage_count,0);
 for(const q of [-1,1.5,true,1000000000,'3',null]) await assert.rejects(save(q));
});
test('storage failures never claim success',async()=>{
 const broken={getItem:()=>null,setItem:()=>{throw Error('quota')}};
 await assert.rejects(cloudApi(async()=>plan,()=>broken)('/api/inventory',{body:'{"material_id":1,"quantity":0}'}));
 await assert.rejects(cloudApi(async()=>plan,()=>({getItem:()=>'{'}))('/api/plan?'));
});
test('range and integer validation',()=>{
 for(const q of ['to_phase=7','from_phase=5&to_phase=2','attack_to=0','skill_to=11','character_id=1.5','burst_to=NaN']) assert.throws(()=>selection(new URLSearchParams(q)));
 assert.equal(selection(new URLSearchParams('to_phase=0')).to_phase,0);
});

import {spawnSync} from 'node:child_process';
import {readFileSync,readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
test('deterministic migration and fail-closed asset allowlist',()=>{
 const cwd=fileURLToPath(new URL('.',import.meta.url));
 for(let i=0;i<2;i++) {const r=spawnSync('python',['prepare.py'],{cwd,encoding:'utf8'});assert.equal(r.status,0,r.stderr);}
 const r=spawnSync('python',['-c',`import sqlite3;from pathlib import Path
s=Path('migrations/0001_standard_data.sql').read_text(encoding='utf-8')
d=sqlite3.connect(':memory:');d.executescript(s)
assert d.execute('SELECT COUNT(*) FROM inventory').fetchone()[0]==0
assert not d.execute('PRAGMA foreign_key_check').fetchall()
try:d.executescript(s)
except sqlite3.OperationalError:pass
else:raise AssertionError('Repeated import did not fail')`],{cwd,encoding:'utf8'});
 assert.equal(r.status,0,r.stderr);
 const walk=(path)=>readdirSync(path,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path+'/'+e.name):[path+'/'+e.name]);
 assert.equal(walk(cwd+'public').length,7);
 assert.ok(!walk(cwd+'public').some(p=>/\.(webp|png|jpg|db)$/.test(p)));
 assert.deepEqual(JSON.parse(readFileSync(cwd+'public/images/characters/manifest.json','utf8')),{characters:{}});
});
