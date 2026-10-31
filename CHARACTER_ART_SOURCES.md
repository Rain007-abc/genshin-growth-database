# 角色图片来源与匹配记录

核验日期：2026-10-29。用途：本机、非商业数据库课堂演示；没有上传或发布图片。

## 覆盖结果

- 完整立绘：120 / 120；仅头像：0；缺失：0。占位图不计入成功。
- 角色 ID / slug / 中英文名称匹配失败名单：无。全部 240 个文件已解码、核对尺寸、透明通道和 SHA-256；没有跨角色重复图片。
- 原始 PNG 合计 158.28 MB；本地 WebP 合计 111.35 MB，减少 29.65%。
- 立绘使用原始完整画布与原尺寸的无损 WebP；头像等比缩小到最长边 96 px，保留透明背景。页面以 object-fit: contain 显示。

## 实际使用来源与条件

1. [ScobbleQ/HoYo-Assets](https://github.com/ScobbleQ/HoYo-Assets)：96 位角色的立绘与头像。固定提交 `9324d91d6bd5719223efed4236638cd9b75ca1f8`；下载路径为 `genshin/splash/<ID>.png` 和 `genshin/icon/<ID>.png`。README 表示任何人可使用，并明确美术归 HoYoverse；说明存档于 `data/character_art_sources/HoYo-Assets-README.txt`。文件另核对 Git blob SHA-1。仓库首页标注的旧版本不能代表实际覆盖，实际与 SQLite 的 120 个 ID 逐一求交得到 96。
2. [Yatta 素材站](https://gi.yatta.moe)：补足 24 位角色的立绘与头像，图片地址为 `https://gi.yatta.moe/assets/UI/<游戏内部标识>.png`，每张的精确地址、大小和 SHA-256 见 manifest。服务器不提供固定图片版本，已下载到本地固定保存。此次能够取得这些精确图片地址，但其首页/API 对部分请求返回 403，未取得可将游戏美术重新授权的素材许可文本；不声称该站或本项目获得 HoYoverse 正式授权。没有绕过登录或访问保护。
3. [theBowja/genshin-db](https://github.com/theBowja/genshin-db)：只用作身份及图片标识索引，没有从中下载角色美术。角色 ID/英文名记录及 `src/data/image/characters.json` 均核验到现有数据快照提交 `49a6544a6c6ae36089cb42fa591fc46f01de8bcf`（图片索引 blob `7842ed8f958e5292b87a1fbc7fed58c258c139bf`）。其 MIT 许可不能解释为游戏图片使用授权。

**版权边界：** 图片版权仍属于 HoYoverse / miHoYo 及相关权利人（联动角色可能涉及其他权利人）。素材搬运站的说明及代码仓库许可证不等于游戏图片授权。本次仅按用户指定用途保存在本机，保留来源；不授予公开分发、商业使用或再许可权利。公开发布或改变用途前需要另行核实相关权利人的使用要求。

## 调查但未采用

- [CMHopeSunshine/GenshinWikiMap](https://github.com/CMHopeSunshine/GenshinWikiMap)，提交 `7fafe2e18011008d47e347f0f68216d05da0c1f1`：资源较旧，未补齐全部角色。README 声明资料版权属于米哈游、仅供学习交流；传播或在其他项目使用制作好的游戏图鉴须先联系作者，私人使用无需。未下载其成品图鉴或美术；GPL-3.0 不能等同于美术授权。
- [EnkaNetwork/API-docs](https://github.com/EnkaNetwork/API-docs)：调查过角色 ID/内部标识表；图片端点返回 403，因此没有采用其图片，也没有将它算作实际素材来源。

## 匹配与本地管理

- HoYo-Assets：数据库数值 ID 精确匹配文件名；同时将 `gi_characters.json` 的内部标识与 genshin-db 对应精确 slug 的头像标识交叉核验。
- 补充角色：读取固定提交下 `English/characters/<数据库slug>.json`，要求 ID 与英文名同时完全一致；再以同一提交的图片索引取得内部标识。没有拼写相似度、模糊中文名、搜索图片或自动借用其他角色。
- 命名：`static/images/characters/<ID>.webp` 为完整立绘；`<ID>-avatar.webp` 为头像。`placeholder.svg` 是本项目绘制的通用几何占位图。
- `static/images/characters/manifest.json` 包含每个角色的中英文名、ID、slug、来源 URL、匹配方法、原图及本地 SHA-256、尺寸、体积和缺失错误。
- `data/character_art_sources/` 保存候选资源索引、身份核验、审计 JSON 和三张全角色核对缩略图。它们仅供开发核验，不由网站静态路由公开提供。
- 网站运行不联网：列表头像 loading="lazy"；详情只请求当前角色的立绘，异步解码；缺图/加载错误统一显示占位图，manifest 不可用时养成 API 仍可用。
- 维护脚本 `scripts/download_character_art.py` 和 `scripts/audit_character_art.py` 需 Pillow；本次使用已有的 Codex 随附 Python/Pillow，无需安装新包。日常 `run_windows.bat` / `python app.py` 仍只需 Python 标准库。

## 逐角色清单

| ID | slug | 中文名 | English | 立绘 | 头像 | 素材来源 |
| --- | --- | --- | --- | --- | --- | --- |
| 10000002 | kamisatoayaka | 神里绫华 | Kamisato Ayaka | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000003 | jean | 琴 | Jean | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000006 | lisa | 丽莎 | Lisa | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000014 | barbara | 芭芭拉 | Barbara | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000015 | kaeya | 凯亚 | Kaeya | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000016 | diluc | 迪卢克 | Diluc | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000020 | razor | 雷泽 | Razor | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000021 | amber | 安柏 | Amber | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000022 | venti | 温迪 | Venti | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000023 | xiangling | 香菱 | Xiangling | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000024 | beidou | 北斗 | Beidou | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000025 | xingqiu | 行秋 | Xingqiu | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000026 | xiao | 魈 | Xiao | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000027 | ningguang | 凝光 | Ningguang | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000029 | klee | 可莉 | Klee | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000030 | zhongli | 钟离 | Zhongli | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000031 | fischl | 菲谢尔 | Fischl | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000032 | bennett | 班尼特 | Bennett | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000033 | tartaglia | 达达利亚 | Tartaglia | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000034 | noelle | 诺艾尔 | Noelle | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000035 | qiqi | 七七 | Qiqi | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000036 | chongyun | 重云 | Chongyun | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000037 | ganyu | 甘雨 | Ganyu | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000038 | albedo | 阿贝多 | Albedo | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000039 | diona | 迪奥娜 | Diona | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000041 | mona | 莫娜 | Mona | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000042 | keqing | 刻晴 | Keqing | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000043 | sucrose | 砂糖 | Sucrose | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000044 | xinyan | 辛焱 | Xinyan | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000045 | rosaria | 罗莎莉亚 | Rosaria | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000046 | hutao | 胡桃 | Hu Tao | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000047 | kaedeharakazuha | 枫原万叶 | Kaedehara Kazuha | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000048 | yanfei | 烟绯 | Yanfei | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000049 | yoimiya | 宵宫 | Yoimiya | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000050 | thoma | 托马 | Thoma | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000051 | eula | 优菈 | Eula | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000052 | raidenshogun | 雷电将军 | Raiden Shogun | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000053 | sayu | 早柚 | Sayu | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000054 | sangonomiyakokomi | 珊瑚宫心海 | Sangonomiya Kokomi | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000055 | gorou | 五郎 | Gorou | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000056 | kujousara | 九条裟罗 | Kujou Sara | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000057 | aratakiitto | 荒泷一斗 | Arataki Itto | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000058 | yaemiko | 八重神子 | Yae Miko | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000059 | shikanoinheizou | 鹿野院平藏 | Shikanoin Heizou | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000060 | yelan | 夜兰 | Yelan | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000061 | kirara | 绮良良 | Kirara | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000062 | aloy | 埃洛伊 | Aloy | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000063 | shenhe | 申鹤 | Shenhe | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000064 | yunjin | 云堇 | Yun Jin | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000065 | kukishinobu | 久岐忍 | Kuki Shinobu | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000066 | kamisatoayato | 神里绫人 | Kamisato Ayato | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000067 | collei | 柯莱 | Collei | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000068 | dori | 多莉 | Dori | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000069 | tighnari | 提纳里 | Tighnari | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000070 | nilou | 妮露 | Nilou | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000071 | cyno | 赛诺 | Cyno | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000072 | candace | 坎蒂丝 | Candace | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000073 | nahida | 纳西妲 | Nahida | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000074 | layla | 莱依拉 | Layla | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000075 | wanderer | 流浪者 | Wanderer | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000076 | faruzan | 珐露珊 | Faruzan | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000077 | yaoyao | 瑶瑶 | Yaoyao | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000078 | alhaitham | 艾尔海森 | Alhaitham | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000079 | dehya | 迪希雅 | Dehya | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000080 | mika | 米卡 | Mika | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000081 | kaveh | 卡维 | Kaveh | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000082 | baizhu | 白术 | Baizhu | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000083 | lynette | 琳妮特 | Lynette | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000084 | lyney | 林尼 | Lyney | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000085 | freminet | 菲米尼 | Freminet | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000086 | wriothesley | 莱欧斯利 | Wriothesley | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000087 | neuvillette | 那维莱特 | Neuvillette | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000088 | charlotte | 夏洛蒂 | Charlotte | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000089 | furina | 芙宁娜 | Furina | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000090 | chevreuse | 夏沃蕾 | Chevreuse | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000091 | navia | 娜维娅 | Navia | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000092 | gaming | 嘉明 | Gaming | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000093 | xianyun | 闲云 | Xianyun | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000094 | chiori | 千织 | Chiori | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000095 | sigewinne | 希格雯 | Sigewinne | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000096 | arlecchino | 阿蕾奇诺 | Arlecchino | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000097 | sethos | 赛索斯 | Sethos | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000098 | clorinde | 克洛琳德 | Clorinde | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000099 | emilie | 艾梅莉埃 | Emilie | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000100 | kachina | 卡齐娜 | Kachina | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000101 | kinich | 基尼奇 | Kinich | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000102 | mualani | 玛拉妮 | Mualani | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000103 | xilonen | 希诺宁 | Xilonen | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000104 | chasca | 恰斯卡 | Chasca | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000105 | ororon | 欧洛伦 | Ororon | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000106 | mavuika | 玛薇卡 | Mavuika | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000107 | citlali | 茜特菈莉 | Citlali | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000108 | lanyan | 蓝砚 | Lan Yan | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000109 | yumemizukimizuki | 梦见月瑞希 | Yumemizuki Mizuki | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000110 | iansan | 伊安珊 | Iansan | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000111 | varesa | 瓦雷莎 | Varesa | 完整 | 已取得 | ScobbleQ/HoYo-Assets |
| 10000112 | escoffier | 爱可菲 | Escoffier | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000113 | ifa | 伊法 | Ifa | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000114 | skirk | 丝柯克 | Skirk | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000115 | dahlia | 塔利雅 | Dahlia | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000116 | ineffa | 伊涅芙 | Ineffa | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000119 | lauma | 菈乌玛 | Lauma | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000120 | flins | 菲林斯 | Flins | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000121 | aino | 爱诺 | Aino | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000122 | nefer | 奈芙尔 | Nefer | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000123 | durin | 杜林 | Durin | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000124 | jahoda | 雅珂达 | Jahoda | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000125 | columbina | 哥伦比娅 | Columbina | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000126 | zibai | 兹白 | Zibai | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000127 | illuga | 叶洛亚 | Illuga | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000128 | varka | 法尔伽 | Varka | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000129 | lohen | 洛恩 | Lohen | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000130 | linnea | 莉奈娅 | Linnea | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000131 | nicole | 尼可 | Nicole | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000132 | prune | 布伦妮 | Prune | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000133 | sandrone | 桑多涅 | Sandrone | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000140 | vodyanitsa | 沃雅妮莎 | Vodyanitsa | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000143 | vesna | 薇斯纳 | Vesna | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000148 | alyosha | 阿罗夏 | Alyosha | 完整 | 已取得 | Yatta (Project Amber successor) |
| 10000150 | odette | 奥黛塔 | Odette | 完整 | 已取得 | Yatta (Project Amber successor) |
