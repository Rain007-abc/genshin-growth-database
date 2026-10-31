# 角色图片功能验证记录

验证日期：2026-10-29。直接修改当前文件夹，没有生成 ZIP 或发布至公开平台。

## 开发前状态

- 当前文件夹没有 `.git` 元数据，`git status` 返回不是 Git 仓库，因此无法区分未提交修改；没有执行重置、清理或覆盖用户文件。
- 修改前的 `app.py`、`static/index.html`、`static/app.js`、`static/style.css` 已复制到 `local_backups/character-art-before/`。
- 保存了受保护源文件 SHA-256，以及 SQLite 的结构和逻辑导出 SHA-256。SQLite 当时被其他进程打开，PowerShell 无法取得整个数据库文件的字节哈希，因此使用只读 SQLite 逻辑导出验证。

## 试点先于批量导入

首先仅导入香菱（火）、行秋（水）、丽莎（雷）、凯亚（冰）、温迪（风）五位角色。浏览器逐项切换，核验图片地址与所选角色 ID 对应、图片加载成功、材料计划仍可显示、立绘与下方操作面板不重叠；检查桌面及 390 px 手机布局后才导入剩余角色。

## 全量图片核验

- 完整立绘 **120**；仅头像 **0**；无图片 **0**；ID/内部标识匹配失败名单：**无**。占位图不计入成功。
- `scripts/audit_character_art.py` 已读取实际 SQLite 中的 120 个角色，逐一核对 manifest 的 ID、slug、中英文名和上游图片内部标识。
- 解码全部 **240** 张本地 WebP，核验文件 SHA-256、图片尺寸、透明通道及无损标识；所有立绘保持原尺寸，没有拉伸或裁掉画布。
- 全部图片没有跨角色重复原图哈希。三个全角色带 ID/英文名的核验缩略图已查看，保存在 `data/character_art_sources/contact-sheet-1.jpg` 至 `contact-sheet-3.jpg`。
- 图片合计从 158,280,718 字节减少到 111,347,742 字节，减少约 29.65%。列表头像为最长边 96 px；完整立绘仅选中时请求。

## 浏览器功能验证

- 原有 120 位角色列表、中英文搜索、元素筛选均正常；搜索 Nahida 后选择草元素显示 1 位，切换火元素显示无匹配结果。
- 香菱突破目标切换到 6 阶后，绝云椒椒需求为 168、常燃火种为 46，材料清单正常刷新；未改动材料计算代码。
- 在仅用于测试的 SQLite 副本上操作网页库存，将绝云椒椒设为 168，缺口显示“已足够”；刷新页面后仍为 168。实际项目库存保持原值。
- 在隔离测试服务器上人为让香菱头像及立绘请求返回 404，网页均回退到本地占位图，显示“立绘暂不可用”；计算、库存保存仍可用。
- 320、390、768、1280 px 四种宽度检查均无页面横向溢出，`scrollWidth == clientWidth`；立绘始终在规划操作区域上方，`object-fit: contain`，不遮挡操作控件。
- `data/character_art_sources/desktop-preview.jpg` 保存最终桌面截图。

## 自动化测试

命令：

```powershell
python -m unittest discover -s tests -v
node --check static/app.js
```

结果：**11 项测试全部通过**；JavaScript 语法检查通过。其中原有 6 项数据库测试，以及新增 5 项图片与 API 回归测试。

新增测试覆盖 manifest 与实际 120 个 ID 精确对应、全部 240 个本地图片路由及 MIME、占位图和缺图 404、路径穿越/任意文件请求被拒绝、计划和库存 API（库存只写测试副本）。

原有测试在 Windows 清理临时数据库时发现连接尚未释放：只在 `tests/test_database.py` 的清理阶段增加垃圾回收，不改动 `planner.py` 或 `init_db.py`。原有测试构建的是临时数据库，不是项目的 `genshin_growth.db`。

## 数据及运行方式

- `genshin_growth.db` 的结构和逻辑内容与开发前一致；未重建、未写入或更新现有养成数据/库存。
- `schema.sql`、`init_db.py`、`planner.py`、`data/source_snapshot.json`、`run_windows.bat` 的 SHA-256 与开发前一致。
- 双击 `run_windows.bat`，或在当前目录执行 `python app.py`；浏览器访问 `http://127.0.0.1:8765`。没有新增网站运行依赖。
- 图片导入/审计脚本才需要 Pillow，本次使用已经存在的随附运行时；日常启动不运行这些维护脚本。
