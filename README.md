# 提瓦特养成计划 — Genshin Growth Database

一个为 Database 课程准备的、**已经可运行**的《原神》角色养成数据库演示项目。它重点展示关系型数据库，而非单纯静态网页。

## 功能

- 收录 **120 位**拥有标准角色突破和天赋升级表的角色，**309 种**关联材料。
- 从当前突破阶段规划到目标阶段（0–6），并独立设置普通攻击 / 元素战技 / 元素爆发的起止天赋等级（1–10）。
- 根据开源材料成本逐级汇总，减去本地保存的背包数量，显示真实的材料缺口。
- 按材料类别排序，显示一般性获取方向；部分天赋书标注秘境开放日。
- 修改背包数量后执行 SQLite `INSERT ... ON CONFLICT DO UPDATE`，刷新后仍可保留。
- 无需联网、无登录、无额外 Python 第三方依赖。

**范围提醒：** 此版本是课程原型，不提供队伍 DPS 最优解、抽卡建议、武器/圣遗物/角色经验书统计或树脂耗时最优解。掉落存在随机性，数据不能当作游戏内保证。旅行者等非统一成长表角色暂未收录。

## Windows 运行（推荐）

1. 克隆仓库或解压完整项目，**不要只打开一个 HTML 文件**。
2. 电脑安装 Python 3.10 或更新版本（建议 3.12）。
3. 双击 `run_windows.bat`。脚本会先尝试可用的 `python`，再尝试 `py -3`。
4. 浏览器打开 **http://127.0.0.1:8765**。
5. 使用后在命令行窗口按 `Ctrl+C` 停止服务。

当前原始本地项目已有完整的 `genshin_growth.db`，无需重新建表。GitHub 仓库不包含这份可变数据库；首次克隆后，在项目目录执行 `python init_db.py` 创建自己的本地数据库，再双击启动脚本（无需安装第三方包）。初始化包含演示库存，不是原用户的库存；已有数据库时脚本拒绝覆盖。如果端口被占用，可用 `python app.py --port 8766`，再打开对应端口。

### Windows 启动故障排查

如果窗口提示 `No working Python 3.10 or newer was found`，请进入解压后的 `genshin_growth` 文件夹，在资源管理器地址栏输入 `cmd` 并按 Enter，再依次执行：

```bat
python --version
py -0p
where python
```

- 如果 `python --version` 显示 **Python 3.10 或更新版本**，可以在同一窗口直接运行 `python app.py`，之后访问 `http://127.0.0.1:8765`。
- 如果 `py -0p` 或报错显示 `C:\python2\python.exe` 等已经不存在的位置，说明 Windows 的 Python 启动器仍保存了过期路径；应修复或重新安装 Python，并再次测试 `python --version`。不需要把程序复制到那个路径。
- 如果以上命令都无法启动 Python，请从 Python 官方网站安装 3.10 或更新版本后重新打开命令提示符。程序本身不依赖任何第三方 Python 包。
- 如仍失败，请复制**完整命令行报错**以及上述三个命令的输出，便于区分 Python 安装问题和程序问题。

`run_windows.bat` 特意使用纯英文 ASCII 命令以及 Windows 兼容的换行编码，以避免某些命令提示符对中文脚本的乱码误解析。

其他系统：在项目目录运行 `python3 app.py`。

## Database Design（数据库设计）

设计目标是用关系型数据库保存角色与材料的逐级需求，结合本地库存计算养成缺口，并为课程演示提供可解释的主键、外键和关联查询。完整关系图与字段说明见 [ERD.md](ERD.md)，建表定义以 `schema.sql` 为准。

### 为什么使用六张表

角色和材料分别保存基本属性；两张需求表分别保存突破阶段和天赋等级的成本；库存保存可变的本地数量；来源表保存整个快照的来源与版本。这样既能避免在每条需求中重复角色和材料名称，也能让库存编辑不影响标准成本。

| 表 | 内容 | 主键 | 关系 |
| --- | --- | --- | --- |
| `characters` | 角色信息 | `id` | 角色 1:N 升级材料需求 |
| `materials` | 材料名称、分类、采集提示 | `id` | 材料 1:N 升级材料需求 |
| `ascension_requirements` | 每位角色每次突破所需的材料及数量 | `(character_id, phase, material_id)` | 两个外键 |
| `talent_requirements` | 每位角色单项天赋每次升级需要的材料及数量 | `(character_id, to_level, material_id)` | 两个外键 |
| `inventory` | 本地演示玩家的材料库存 | `material_id` | 材料到库存为 1:0..1 |
| `data_sources` | 数据来源与版本 | `source_name` | 独立来源表 |

### 关系与复合主键

角色与材料之间是多对多关系（Many-to-Many，M:N）。两个需求关联表（Junction Table）分别连接角色与材料，把 M:N 转换为两侧的一对多关系（One-to-Many，1:N）。每条需求只能引用一个存在的角色和一种存在的材料。

复合主键（Composite Primary Key）防止同一角色、同一突破阶段或天赋目标等级重复登记同一种材料。需求中的 `quantity` 是单次升级的增量成本，不是累计成本：`phase = 1` 表示突破 0→1 阶，`to_level = 2` 表示天赋 1→2 级。

`inventory.material_id` 同时是主键（Primary Key）和外键（Foreign Key），因此一种材料可以没有库存记录，也最多只有一条；这不是 1:N 关系。`data_sources` 是独立来源元数据表，没有指向业务表的外键。

### 建模假设与适用范围

- **统一天赋配方：** 对每位已收录角色，普通攻击、元素战技和元素爆发在相同等级共用一套成本记录，因此没有 `talent_type` 字段。三个天赋可以设置不同的起止等级，程序逐项累加；全部从 1 升到 10 时，同一套完整配方计入三次。本原型不覆盖所有特殊成长规则。
- **单本地库存：** 没有玩家表或玩家编号，不同角色计划读取同一个本地背包。生成计划不会扣减或预留材料；缺少库存记录时按 0 处理，缺口为 `max(0, 总需求 - 已有数量)`。只有手动编辑背包时才保存数量。
- **固定数据快照：** 业务数据来自同一份离线快照，`data_sources` 记录统一来源，不提供逐行来源追踪。固定提交号和快照日期见下方“数据来源、许可及限制”；它们不等同于游戏版本号。

### Normalization（规范化）

| 范式 | 当前设计与取舍 |
| --- | --- |
| First Normal Form（第一范式，1NF） | 核心需求表按“角色＋阶段或等级＋材料”逐行保存，没有将多个材料编号合并存储。`farm_days` 则保留“周一、周四、周日”这样的多值展示文本；若将开放日视为可独立查询和约束的数据，应拆为关联记录。当前仅作展示，不把它称为严格规范化的开放日模型。 |
| Second Normal Form（第二范式，2NF） | 在当前业务定义下，需求数量由完整的复合键确定；需求表没有重复保存只依赖角色编号或材料编号的名称等属性，未发现明显的部分依赖（Partial Dependency）。 |
| Third Normal Form（第三范式，3NF） | 角色、材料、需求和库存已经分离，但当前 `farm_hint` 由类别统一生成，存在 `material_id → category → farm_hint` 的传递依赖（Transitive Dependency）和重复文本。若按严格 3NF 整理，应将类别通用提示独立保存或在展示时生成。 |

当前保留 `farm_days` 和 `farm_hint` 是为了简化课程原型的展示与数据读取，并不表示数据库严格满足所有范式。开放日空字符串表示未记录信息，不能解释为没有开放日。是否需要进一步拆分，应结合教师对规范化的要求决定；现有实现没有为此更改结构。

### SQL、Python 与 JavaScript 的分工

| 层次 | 实际实现 |
| --- | --- |
| SQL 查询与聚合 | `planner.py` 使用 `SELECT`、`WHERE` 查询角色和逐级需求，以 `LEFT JOIN`、`COALESCE` 联查库存；`app.py` 使用 `COUNT(*)` 统计数量。`sql/demo_queries.sql` 另提供 `JOIN`、`SUM`、`GROUP BY` 和 CTE 的课堂聚合查询。 |
| Python 材料累加 | `calculate_plan()` 将突破及三个天赋各自升级区间的需求按材料编号累加，再计算缺口、排序并返回结果。网页计划的主要需求汇总在 Python 中完成，不是由 SQL `GROUP BY` 完成。 |
| JavaScript 角色筛选 | `static/app.js` 取得角色列表后，用浏览器中的 `filter()` 按中英文名称和元素筛选；这部分不是后端 SQL `WHERE` 查询。 |

库存写入由 `planner.py` 中的 `INSERT ... ON CONFLICT DO UPDATE` 完成：没有该材料的库存行时新增，已有时更新。它是实际实现的 UPSERT，不是单独的 `UPDATE ... WHERE ...` 演示语句。

## 一段 10 分钟的课堂演示

1. 0–2 分钟：介绍游戏养成的材料计算问题，展示 E-R 图。
2. 2–4 分钟：在 SQLite 中展示六张表、主键、外键与关联表。
3. 4–6 分钟：打开网页选择香菱，设置突破/天赋目标，生成材料清单。
4. 6–8 分钟：编辑一项背包库存，观察缺口减少；打开 SQL 演示查询。
5. 8–10 分钟：解释 `JOIN`、`SUM`、外键约束，展示数据来源与局限。

本项目是课程原型，当前目录未附教师正式任务书或评分标准。是否接受 SQLite、是否要求先审批 E-R 图、是否要求严格第三范式及独立的增删改 SQL 演示，应向教师确认。课堂展示应注明开源数据来源，不应将其说成小组自行收集或制作的数据。

## 验证

```bash
python -m unittest discover -s tests -v
python app.py
```

程序使用 Python 标准库，不依赖 MySQL 或 Flask。若老师指定 MySQL，可以把当前 SQLite 表结构和数据映射迁移过去；不必为第一版增加前端框架或服务器部署。

## 重新生成数据库（可选）

原始本地项目中的 `genshin_growth.db` 已包含数据，但不会提交到 GitHub。新克隆的项目在数据库不存在时可运行 `python init_db.py`，从 `schema.sql` 和 `data/source_snapshot.json` 初始化。`init_db.py` 故意**不会覆盖现有数据库和背包库存**；若要重新生成数据库，请显式传入新的数据库输出路径：

```python
from init_db import build_database
build_database("my_fresh_database.db")
```

更新上游数据时先获取源仓库，在包含中英文数据目录的仓库本地路径下执行：

```bash
python scripts/import_source.py /path/to/genshin-db data/source_snapshot.json
```

数据快照固定为某个 Git commit，避免课堂展示时网络或游戏版本变化影响输出。更新快照后再构建**新**数据库并验证。导入工具只读取 JSON，不执行开源仓库代码。

## 数据来源、许可及限制

- 上游数据：[`theBowja/genshin-db`](https://github.com/theBowja/genshin-db)，基于游戏数据整理的开源项目，许可证 MIT。它并非 HoYoverse 官方授权的第三方工具。
- 本项目使用其 `English` / `ChineseSimplified` 角色、天赋成本字段及已覆盖的天赋书日期字段。具体固定版本记录在 `data/source_snapshot.json` 和 SQLite `data_sources` 表。
- 当前固定 Git commit：`49a6544a6c6ae36089cb42fa591fc46f01de8bcf`；快照日期：`2026-10-22`。数据库保存来源地址、提交号及许可证说明；快照日期和特殊角色排除说明保存在 JSON 中。当前没有明确记录游戏版本号，也不宣称数据为实时或最新版本。
- 游戏内数据以实际客户端为准；本项目没有直接连接、扫描或登录用户的游戏账号。
- 原始资料仅用于课程学习演示，并保留上游许可与署名，见 `THIRD_PARTY_LICENSE.md`。

> 本项目与 HoYoverse /《原神》无隶属或官方认可关系。

## 本地角色头像与立绘

原始本地项目已备有 120 位角色的头像和完整立绘；GitHub 仓库不分发这些游戏图片，也不分发素材预览或联系表。角色列表支持头像延迟加载，选中角色后才加载该角色的大图；图片失效时显示统一占位图。日常启动方式与养成计算、库存 API 保持不变，无新增运行依赖。

素材覆盖、逐角色 ID 匹配、来源和使用条件见 [CHARACTER_ART_SOURCES.md](CHARACTER_ART_SOURCES.md)。逐张下载地址、SHA-256、尺寸及体积记录在 `static/images/characters/manifest.json`。图片仅供本机非商业课堂演示，代码仓库许可证不等于游戏美术授权；本次仅提交图片清单和来源记录，不上传图片素材。

开发前原始前端和服务器文件备份位于 `local_backups/character-art-before/`；数据库仅做只读校验，没有重建或修改。素材维护脚本需要 Pillow，网站运行不需要；不要为了启动网页运行素材下载或数据库初始化脚本。


### 克隆后的本地图片准备

仓库保留 `static/images/characters/manifest.json`、原创占位图 `placeholder.svg`、`data/character_art_sources/` 中的文字与 JSON 来源记录，以及素材维护脚本。清单描述原始本地素材，不表示图片文件已随仓库分发。缺图时网页使用占位图，养成计算与库存功能仍可使用。

在确认具备所需使用权限后，可将自行合法取得并与清单匹配的 WebP 文件放到 `static/images/characters/`：立绘为 `<角色ID>.webp`，头像为 `<角色ID>-avatar.webp`。可依据清单中的尺寸、SHA-256 和来源检查文件。现有本地图片无需重新下载或移动。`scripts/download_character_art.py` 是历史素材导入工具，需要 Pillow 且会访问第三方来源、更新本地素材和清单；来源可用性及使用许可需自行确认，它不是启动步骤。本次未运行素材下载脚本。

### Git 管理与验证范围

`.gitignore` 排除运行数据库及其日志、`local_backups/`、游戏图片（含预览）、密钥与环境变量文件、依赖目录和临时缓存。数据库结构、120 位角色的固定快照、前后端代码、E-R 图、来源和许可说明均保留。原始本地备份只保存在本机。

`python -m unittest discover -s tests -v` 可在已准备数据库和完整图片的原始本地环境运行。数据库测试使用临时数据库，图片/API 测试使用当前数据库的隔离副本；图片测试要求清单列出的本地图片存在。新克隆后可先初始化数据库，再运行 `python -m unittest discover -s tests -p test_database.py -v`；未准备图片时完整图片测试不能全部通过。

## Workers + D1 方案（本地验证，尚未部署）

保留原 Windows + Python + SQLite 本地版：双击 `run_windows.bat`，访问 `http://127.0.0.1:8765`，库存仍写入本机 SQLite。

新增 `cloudflare/`：JavaScript Worker 提供只读 API，D1 保存同一标准游戏数据；复用原前端的白名单构建，库存仅保存在当前浏览器 localStorage，初始为零，不跨浏览器或设备同步，清除网站数据会丢失。此方案不会迁移个人库存，也不分发游戏图片；页面使用原创占位图。

Node.js 22+ 和 Python 3.10+ 环境下：

```sh
cd cloudflare
npm ci
npm run db:local
npm run dev
```

访问 `http://127.0.0.1:8787`。所有数据库准备命令仅操作 Wrangler 本地 D1，无需 Cloudflare 登录。详细架构、API、验证命令与后续账号/配置步骤见 [cloudflare/README.md](cloudflare/README.md)。当前尚未创建远程 D1，也未执行 Cloudflare 部署。
