import { sortMaterials } from './plan.js';
const json = (body,status=200) => Response.json(body,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
export function selection(params) {
  function number(key, fallback) {
    const s = params.get(key);
    if (s === null || s === '') return fallback;
    if (!/^[+-]?\d+$/.test(s.trim()) || !Number.isSafeInteger(Number(s))) throw new Error('参数必须为整数');
    return Number(s);
  }
  function range(a,b,lo,hi) { if(a<lo || b>hi || b<a || a>hi || b<lo) throw new Error('升级范围无效'); }
  const from_phase=number('from_phase',0), to_phase=number('to_phase',4);
  range(from_phase,to_phase,0,6);
  const talents = {};
  for (const [key,d] of [['attack',1],['skill',4],['burst',6]]) {
    talents[key] = [number(key+'_from',1),number(key+'_to',d)];
    range(...talents[key],1,10);
  }
  return {character_id:number('character_id',10000023),from_phase,to_phase,talents};
}
export async function plan(db,s) {
  const character=await db.prepare('SELECT * FROM characters WHERE id=?').bind(s.character_id).first();
  if(!character) throw new Error('角色不存在');
  const queries=[db.prepare('SELECT material_id,quantity FROM ascension_requirements WHERE character_id=? AND phase>? AND phase<=?').bind(s.character_id,s.from_phase,s.to_phase),
    ...Object.values(s.talents).map(([a,b])=>db.prepare('SELECT material_id,quantity FROM talent_requirements WHERE character_id=? AND to_level>? AND to_level<=?').bind(s.character_id,a,b))];
  const results=await db.batch(queries);
  const totals=new Map(), labels=['突破','attack','skill','burst'];
  results.forEach((result,i)=>result.results.forEach(({material_id,quantity})=>{
    if(!totals.has(material_id)) totals.set(material_id,{required:0,breakdown:{}});
    const m=totals.get(material_id); m.required+=quantity;
    m.breakdown[labels[i]]=(m.breakdown[labels[i]]||0)+quantity;
  }));
  const materials=sortMaterials((await db.prepare('SELECT * FROM materials').all()).results.filter(m=>totals.has(m.id)).map(m=>{
    const v=totals.get(m.id);return {...m,...v,owned:0,missing:v.required};
  }));
  const cap=[1,1,2,4,6,8,10][s.to_phase];
  return {character,selection:{from_phase:s.from_phase,to_phase:s.to_phase,talents:s.talents},material_count:materials.length,
    shortage_count:materials.length,materials,warnings:Object.values(s.talents).some(([,b])=>b>cap)?[`目标突破阶段 ${s.to_phase} 对应天赋等级上限约为 ${cap}；若要完成更高天赋，请提高突破阶段。`]:[],
    notes:['数量按突破阶段及三个天赋逐级累加；不包含角色经验书、武器、圣遗物。','库存仅保存在当前浏览器，不与游戏账号连接，不跨设备同步。']};
}
export default {
  async fetch(request,env) {
    const url=new URL(request.url), path=url.pathname;
    if(!path.startsWith('/api/')) return env.ASSETS.fetch(request);
    if(request.method!=='GET') return json({error:'在线 API 只读；库存由浏览器保存'},405);
    if(path==='/api/health') return json({ok:true,service:'Genshin Growth',inventory:'localStorage'});
    if(!['/api/characters','/api/stats','/api/plan'].includes(path)) return json({error:'Not found'},404);
    try {
      if(path==='/api/characters') return json((await env.DB.prepare('SELECT * FROM characters ORDER BY name_zh COLLATE NOCASE').all()).results);
      if(path==='/api/stats') {
        const row=await env.DB.prepare(`SELECT (SELECT COUNT(*) FROM characters) characters,(SELECT COUNT(*) FROM materials) materials,
          (SELECT COUNT(*) FROM ascension_requirements) ascension_rows,(SELECT COUNT(*) FROM talent_requirements) talent_rows,
          (SELECT substr(revision,1,10) FROM data_sources WHERE source_name='genshin-db') revision`).first();
        return json(row);
      }
      let s;try{s=selection(url.searchParams);}catch(e){return json({error:e.message},400);}
      const exists=await env.DB.prepare('SELECT id FROM characters WHERE id=?').bind(s.character_id).first();
      if(!exists) return json({error:'角色不存在'},400);
      return json(await plan(env.DB,s));
    } catch(e) { console.error(e);return json({error:'Server error'},500); }
  }
};
