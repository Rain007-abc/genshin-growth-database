# Workers + D1 本地适配（尚未部署）

原 Python / SQLite 架构、业务表定义与 Windows 启动脚本不变。新增 JavaScript Worker 提供只读标准数据与需求计算；Workers Static Assets 提供由原 `static/` 白名单生成的前端。浏览器 localStorage 单独保存库存，初始为零，不迁移 SQLite 个人库存，不跨浏览器、设备或不同网站 origin 同步；清除网站数据会丢失库存。

## 本地启动

需要 Node.js 22 或更新版本、npm、Python 3.10+。在本目录执行：

```sh
npm ci
npm run db:local
npm run dev
```

访问 http://127.0.0.1:8787 。上述 Wrangler 命令显式使用 `--local`；配置中的 D1 ID 是本地占位值，`remote: false`，无需登录 Cloudflare。本阶段不得执行部署、远程建库或远程导入。

`prepare.py` 仅从 JSON 快照在内存中构建标准数据，绝不打开本地 `genshin_growth.db`，保留同一六表结构但 `inventory` 为零行且 Worker 不查询或写入它。输出稳定的 `migrations/0001_standard_data.sql`；若现有迁移与新快照不符则报错。Wrangler migrations 记录已应用版本，重复执行 `npm run db:local` 不重复插入；直接再次执行同一 SQL 会明确失败，不使用 INSERT OR IGNORE。迁移错误会终止命令，不能视为成功。未来更新快照需要新增经过审查的迁移。

## API

- `GET /api/health`：运行状态与浏览器库存模式。
- `GET /api/characters`：角色列表。
- `GET /api/stats`：标准数据记录数与来源 revision。
- `GET /api/plan`：与 Python HTTP API 同名查询参数、默认值、逐级汇总、三项天赋和突破上限提醒；返回零库存需求。浏览器再应用本地库存计算缺口与排序。
- `POST /api/inventory` 不向云端发送：构建的前端适配器保存到 localStorage；直接请求此 API 返回 405。所有 `/api/*` 非 GET 方法均被拒绝，未知 GET 路由为 404。

Worker 的 D1 SQL 全部为固定的参数绑定 SELECT。D1 绑定本身具有数据库权限，“只读”由本 Worker 无写入口保证，不是声称 D1 提供只读凭据。

## 图片及构建边界

`public/` 是被 Git 忽略的生成目录。构建仅复制 HTML、CSS、JS 和原创 SVG 占位图，并生成空图片清单，不复制原游戏图片、预览、原图片清单或来源文件。若目录中出现非白名单文件，构建直接报错。原网页缺图直接显示占位图与说明，不请求第三方 CDN。不要将 Wrangler assets 目录改为原始 `static/`。本地 120 位角色素材保持原样，仅供原本地方案使用，图片授权不因仓库私有或代码许可自动获得。

## 验证

先保持本地 Wrangler 服务运行，另一个终端在本目录执行：

```sh
npm test
npm run test:integration
```

`verify.py` 在内存中载入同一标准迁移，对全部 120 个角色的四种目标组合比较 Python 与实际本地 Worker 返回；再比较浏览器库存覆盖后的结果（零、部分、足够、超额）。另检查网页资源、非法输入和写入拒绝。原有测试在项目根目录执行 `python -m unittest discover -s tests -v`，完整图片测试需要原本地图片与数据库。

## 第三阶段准备（本阶段未执行）

1. Cloudflare 账号需有 Workers 与 D1 权限，确认账户与拟使用的域名/访问地址。届时执行 `npx wrangler login` 和 `npx wrangler whoami`，不要发送凭据到聊天。
2. 明确授权后才创建远程 D1，记录 account ID 与 database ID。使用独立生产配置替换本地占位 ID，保持本地配置不连接远程资源；数据库 ID 不是密码，Token 应通过受保护环境变量管理。
3. 审查迁移与图片白名单，明确授权后再对新空远程 D1 应用迁移、验证记录数与外键；不要上传本地 SQLite 文件或个人库存。
4. 明确授权后才部署 Worker 和白名单资源，验证线上接口、库存隔离及占位图；配置备份、配额监控与回滚方案。

官方参考：[Static Assets bindings](https://developers.cloudflare.com/workers/static-assets/binding/)、[D1 local development](https://developers.cloudflare.com/d1/best-practices/local-development/)。
