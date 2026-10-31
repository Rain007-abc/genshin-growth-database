import { withInventory, validQuantity } from './plan.js';
const KEY = 'genshin-growth.inventory.v1';
export function cloudApi(network, storage = () => globalThis.localStorage) {
  function read() {
    let raw;
    try { raw = storage().getItem(KEY); } catch { throw new Error('浏览器禁止读取本地库存，请允许网站存储'); }
    if (raw === null) return {};
    let stocks;
    try { stocks = JSON.parse(raw); } catch { throw new Error('本地库存数据损坏，请备份后清除此网站库存数据'); }
    if (!stocks || Array.isArray(stocks) || typeof stocks !== 'object' || Object.entries(stocks).some(([id,q])=> !/^[1-9]\d*$/.test(id) || !validQuantity(q)))
      throw new Error('本地库存格式无效，请备份后清除此网站库存数据');
    return stocks;
  }
  return async (path, options) => {
    if (path === '/api/inventory') {
      const {material_id,quantity} = JSON.parse(options.body);
      if (!Number.isSafeInteger(material_id) || material_id<=0 || !validQuantity(quantity)) throw new Error('背包数量必须是 0 到 999999999 的整数');
      const stocks = read();
      stocks[material_id] = quantity;
      try { storage().setItem(KEY,JSON.stringify(stocks)); } catch { throw new Error('无法保存库存：浏览器存储被禁用或空间不足'); }
      return {ok:true,quantity};
    }
    const result = await network(path,options);
    return path.startsWith('/api/plan?') ? withInventory(result,read()) : result;
  };
}
