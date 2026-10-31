# 正式部署记录

2026-11-01（北京时间）首次使用 Wrangler 部署，控制台确认 Workers Free 当前计划；没有升级或绑定支付方式。GitHub 仓库保持 PRIVATE。公开内容仅为网站白名单资源与标准游戏数据，不包含私有仓库源码、个人库存或游戏图片。

- Worker：`genshin-growth-database`
- 正式网址：https://genshin-growth-database.genshin-growth-cloudflare.workers.dev/
- D1：`genshin-growth-d1`
- D1 ID：`86c2dca4-9090-432f-90c6-34588bccf9f0`
- 首次 Worker Version ID：`d7f2597b-3969-457f-bdf2-e6612362106b`

顶层 `wrangler.jsonc` 为生产绑定；`env.local` 保留原本地 D1 名称与 ID。日常 `npm run dev` / `npm run db:local` 继续显式使用 local 环境。`remote: false` 防止本地开发代理到生产 D1，不影响正式部署绑定。原 Python + SQLite 和 `run_windows.bat` 不变。

## 远程数据与部署

已检查资源无冲突，创建全新数据库，确认空库后仅应用 `0001_standard_data.sql`。迁移不含库存 INSERT、DROP 或 DELETE。实际远程记录数：characters 120，materials 309，ascension_requirements 3480，talent_requirements 3840，inventory 0，data_sources 1。外键检查为空，两张需求表的复合键重复计数均为 0。

首次执行了 `npx wrangler d1 migrations apply DB --remote` 与 `npx wrangler deploy`。未来修改数据库前应先检查 migrations 状态和当前数据；不要重跑原始 SQL，不要把迁移放入每次网站构建命令。

部署前的 Wrangler custom build 执行 `python prepare.py`，仅生成白名单资源。实际上传 7 个文件：index.html、style.css、app.js、inventory.js、plan.js、空图片 manifest.json 和原创 placeholder.svg。Wrangler 可能向构建目录生成自己的控制文件，它们不属于网站素材；再次构建发现任何未知文件仍会报错，必须检查原因。

## 验收结果与复现

公网首页、CSS、JavaScript、占位图正常；health、characters、stats、plan 通过 HTTP 验收。香菱与丝柯克各四种目标（突破、满天赋、混合区间、无增量）共 8 组与 Python 结果一致，再以零、部分、足够、超额库存验证 8 组浏览器覆盖结果。直接 POST/PUT/DELETE 库存 API 返回 405，非法参数返回 400，未分发游戏图片返回 404。

浏览器实际编辑库存并刷新后数值保留，测试值已恢复为零；远程库存表仍为 0 行。390px 手机布局无横向溢出，已加载图片没有破损图标。原有 11 项 Python 测试和 4 组云端关键测试通过。

可在本目录复现公网验收：

```sh
python verify.py --base-url https://genshin-growth-database.genshin-growth-cloudflare.workers.dev --slugs xiangling skirk
```

如本机网络需要代理，可显式增加 `--proxy http://127.0.0.1:<自己的代理端口>`。验收脚本保持 TLS 证书验证，连接异常最多重试 4 次，HTTP 错误不会被吞掉。首次创建 workers.dev 子域名后曾短暂出现 TLS 失败；之后浏览器及经现有代理的实际 HTTP 验收通过。不同网络的 workers.dev 可达性可能不同。

## GitHub 自动部署（尚未连接）

控制台显示需要连接 Git repository，当前正式部署来源是 Wrangler，不能视为已完成 GitHub 自动部署。下一步由账号所有者在 Worker 的 Settings / Builds 连接 GitHub，授权 Cloudflare 访问指定私有仓库即可，无需公开仓库。

配置值：

| 项目 | 值 |
| --- | --- |
| 仓库 | Rain007-abc/genshin-growth-database |
| Worker 名称 | genshin-growth-database |
| 生产分支 | main |
| 根目录 | cloudflare |
| 构建命令 | npm ci && python prepare.py && npm test |
| 部署命令 | npx wrangler deploy --env="" |
| Node.js | 24（NODE_VERSION=24） |
| Python | 3.12（PYTHON_VERSION=3.12） |

构建不执行 D1 迁移。初次建议禁用非生产分支自动部署，以免让预览版本使用生产 D1；如需预览应另建隔离数据库与配置。授权完成后应触发一次 main 构建，检查构建日志及线上版本，再确认自动部署完成。

Workers Builds 不会替代这里显式填写的构建命令；构建镜像提供 Node.js 和 Python。参考 [Builds configuration](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/) 与 [Build image](https://developers.cloudflare.com/workers/ci-cd/builds/build-image/)。
