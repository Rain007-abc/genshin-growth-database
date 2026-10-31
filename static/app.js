const state = { characters: [], selected: null, element: '全部', search: '' };
const $ = id => document.getElementById(id);
const ESC = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ELEMENTS = ['全部','火','水','雷','冰','风','岩','草'];
const COLORS = {'火':'#ad5b4d','水':'#357ea1','雷':'#855baf','冰':'#578a9b','风':'#4a9786','岩':'#aa8c51','草':'#5e925b'};
const ART_ROOT = '/images/characters/';
const ART_PLACEHOLDER = ART_ROOT + 'placeholder.svg';
let characterImages = {};
let toastTimer;

function imagePath(c, kind) {
  const path = characterImages[c.id]?.[kind];
  const expected = `${ART_ROOT}${c.id}${kind === 'avatar' ? '-avatar' : ''}.webp`;
  return path === expected ? path : null;
}
function updateCharacterArt(c) {
  const path = imagePath(c, 'splash');
  const img = document.createElement('img');
  img.id = 'heroArt'; img.width = 640; img.height = 360; img.decoding = 'async';
  img.alt = path ? `${c.name_zh}完整角色立绘` : `${c.name_zh}：暂无完整立绘`;
  $('characterArt').style.setProperty('--character-color', COLORS[c.element] || '#72cfc7');
  $('artStatus').textContent = path ? '正在加载立绘…' : '暂无完整立绘';
  img.addEventListener('load', () => {
    if ($('heroArt') !== img) return;
    $('artStatus').textContent = img.dataset.fallback ? '立绘暂不可用' : (path ? '角色立绘' : '暂无完整立绘');
  });
  img.addEventListener('error', () => {
    if ($('heroArt') !== img || img.dataset.fallback) return;
    img.dataset.fallback = 'true'; img.alt = `${c.name_zh}：立绘暂不可用`;
    $('artStatus').textContent = '立绘暂不可用'; img.src = ART_PLACEHOLDER;
  });
  // Replace the element so an old request cannot update the newly selected hero.
  $('heroArt').replaceWith(img);
  img.src = path || ART_PLACEHOLDER;
}

async function api(path, options) {
  const res = await fetch(path, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || '请求失败');
  return data;
}
function toast(msg) { const el=$('toast');el.textContent=msg;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),3200); }
function options(id, min, max, value, suffix) {
  const el=$(id);el.innerHTML='';
  for(let i=min;i<=max;i++) { const opt=document.createElement('option');opt.value=i;opt.textContent=`${i} ${suffix}`;if(i===value)opt.selected=true;el.appendChild(opt); }
}
function initializeControls() {
  options('from_phase',0,6,0,'阶'); options('to_phase',0,6,4,'阶');
  const fields=[['attack','普通攻击',1],['skill','元素战技',4],['burst','元素爆发',6]];
  $('talentControls').innerHTML=fields.map(([id,label])=>`<div class="talent-row"><span class="talent-title" id="${id}Title">${label}</span><div class="talent-pair"><select id="${id}_from" aria-label="${label}当前等级"></select><span>→</span><select id="${id}_to" aria-label="${label}目标等级"></select></div></div>`).join('');
  fields.forEach(([id,,target])=>{options(`${id}_from`,1,10,1,'级');options(`${id}_to`,1,10,target,'级');});
  document.querySelectorAll('select').forEach(select=>select.addEventListener('change',loadPlan));
}
function updateTalentLabels(char) {
  [['attack','normal_attack','普通攻击'],['skill','elemental_skill','元素战技'],['burst','elemental_burst','元素爆发']].forEach(([id,key,kind])=>{
    $(id+'Title').textContent=`${kind} · ${char[key] || kind}`;
    $(id+'Title').title=char[key]||kind;
  });
}
function renderFilters() {
  $('filters').innerHTML=ELEMENTS.map(e=>`<button class="filter ${state.element===e?'active':''}" data-element="${ESC(e)}">${ESC(e)}</button>`).join('');
  $('filters').querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>{state.element=btn.dataset.element;renderFilters();renderCharacters();}));
}
function renderCharacters() {
  const chars=state.characters.filter(c=>(state.element==='全部'||c.element===state.element) && (c.name_zh.includes(state.search) || c.name_en.toLowerCase().includes(state.search.toLowerCase())));
  $('characterCount').textContent=`显示 ${chars.length} / ${state.characters.length} 位角色`;
  $('characters').innerHTML=chars.length?chars.map(c=>`<button class="character-item ${state.selected?.id===c.id?'active':''}" data-id="${c.id}" aria-pressed="${state.selected?.id===c.id}"><span class="character-portrait" style="--el-bg:${COLORS[c.element]||'#35566d'}"><img src="${imagePath(c,'avatar') || ART_PLACEHOLDER}" alt="" loading="lazy" decoding="async" width="44" height="44"><span class="element-badge">${ESC(c.element.slice(0,1))}</span></span><span class="character-label"><strong>${ESC(c.name_zh)}</strong><small>${ESC(c.name_en)}</small><span class="star-line">${'★'.repeat(c.rarity===5?5:4)}</span></span></button>`).join(''):'<p class="empty">没有匹配的角色</p>';
  $('characters').querySelectorAll('img').forEach(img=>img.addEventListener('error',()=>{img.src=ART_PLACEHOLDER;},{once:true}));
  $('characters').querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>selectCharacter(Number(btn.dataset.id))));
}
function selectCharacter(id) {
  const c=state.characters.find(x=>x.id===id);if(!c)return;
  state.selected=c;
  updateCharacterArt(c);
  $('heroName').textContent=c.name_zh;$('heroEnglish').textContent=c.name_en.toUpperCase();
  $('heroTags').innerHTML=[`${c.element}元素`,c.weapon,c.region,`${c.rarity}星`].map(t=>`<span>${ESC(t)}</span>`).join('');
  updateTalentLabels(c);renderCharacters();loadPlan();
}
function params() {
  const q = new URLSearchParams({character_id:state.selected.id});
  ['from_phase','to_phase','attack_from','attack_to','skill_from','skill_to','burst_from','burst_to'].forEach(id=>q.set(id,$(id).value));
  return q;
}
async function loadPlan() {
  if (!state.selected) return;
  try {
    const data=await api('/api/plan?'+params());
    renderPlan(data);
  } catch(e) {
    $('materialList').innerHTML=`<p class="empty">${ESC(e.message)}</p>`;
    $('warnings').innerHTML='';
    $('statItems').textContent='—';$('statMissing').textContent='—';
    toast(e.message);
  }
}
function num(n) {return Number(n).toLocaleString('zh-CN');}
function categoryGlyph(c) { return ({'地区特产':'❀','世界首领':'◈','天赋书':'▤','周本材料':'✦','敌人掉落':'◆','元素宝石':'◇','智识之冕':'♛','货币':'◉'})[c] || '✧'; }
function renderPlan(data) {
  $('statItems').textContent=num(data.material_count);
  $('statMissing').textContent=num(data.shortage_count);
  $('warnings').innerHTML=data.warnings.map(w=>`<div class="warning">⚠ ${ESC(w)}</div>`).join('');
  if(!data.materials.length){$('materialList').innerHTML='<p class="empty">目标与当前进度相同，暂无新增材料需求。</p>';return;}
  $('materialList').innerHTML=data.materials.map(m=>{
    const hint=[m.farm_hint,m.farm_days?('开放时间：'+m.farm_days):''].filter(Boolean).join(' · ');
    return `<div class="material-row"><div class="mat-title"><span class="mat-icon">${categoryGlyph(m.category)}</span><div class="mat-name"><strong>${ESC(m.name_zh)}<span class="category">${ESC(m.category)}</span></strong><small>${ESC(hint)}</small></div></div><span class="mat-num">${num(m.required)}</span><input class="owned-input" type="number" min="0" max="999999999" step="1" value="${m.owned}" data-material="${m.id}" aria-label="${ESC(m.name_zh)}背包数量"><span class="missing ${m.missing?'':'done'}">${m.missing?num(m.missing):'✓ 已足够'}</span></div>`;
  }).join('');
  $('materialList').querySelectorAll('input').forEach(input=>input.addEventListener('change',async()=>{
    const newValue=Number(input.value);
    if(!Number.isSafeInteger(newValue)||newValue<0){toast('请输入非负整数');return loadPlan();}
    input.disabled=true;
    try{
      await api('/api/inventory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({material_id:Number(input.dataset.material),quantity:newValue})});
      await loadPlan();toast('背包数量已保存');
    }catch(e){toast(e.message);await loadPlan();}
  }));
}
async function start() {
  initializeControls();renderFilters();
  $('search').addEventListener('input',e=>{state.search=e.target.value.trim();renderCharacters();});
  $('calculate').addEventListener('click',loadPlan);
  $('resetSelection').addEventListener('click',()=>{
    const defaults={from_phase:0,to_phase:4,attack_from:1,attack_to:1,skill_from:1,skill_to:4,burst_from:1,burst_to:6};
    Object.entries(defaults).forEach(([id,value])=>$(id).value=String(value));
    loadPlan();toast('已恢复默认养成目标');
  });
  try {
    const [chars,stats,art]=await Promise.all([api('/api/characters'),api('/api/stats'),api(ART_ROOT+'manifest.json').catch(()=>({characters:{}}))]);
    characterImages=art.characters || {};
    state.characters=chars;
    $('statChars').textContent=num(stats.characters);$('statMats').textContent=num(stats.materials);
    $('version').textContent='DATA '+stats.revision;
    selectCharacter(chars.find(c=>c.slug==='xiangling')?.id||chars[0].id);
  }catch(e){$('characters').innerHTML=`<p class="empty">${ESC(e.message)}</p>`;toast('数据库读取失败：'+e.message);}
}
start();
