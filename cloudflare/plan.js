export const categories = ['地区特产','世界首领','天赋书','周本材料','敌人掉落','元素宝石','智识之冕','货币','其他'];
export function sortMaterials(rows) {
  const rank = c => categories.includes(c) ? categories.indexOf(c) : 99;
  return rows.sort((a,b) => rank(a.category)-rank(b.category) || Number(a.missing===0)-Number(b.missing===0) || b.missing-a.missing || (a.name_zh < b.name_zh ? -1 : a.name_zh > b.name_zh ? 1 : 0));
}
export function withInventory(plan, stocks) {
  const materials = sortMaterials(plan.materials.map(m => {
    const owned = stocks[m.id] ?? 0;
    return {...m, owned, missing: Math.max(0,m.required-owned)};
  }));
  return {...plan, materials, shortage_count: materials.filter(m=>m.missing>0).length};
}
export function validQuantity(q) { return Number.isSafeInteger(q) && q>=0 && q<=999999999; }
