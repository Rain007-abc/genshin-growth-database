-- 课堂展示 SQL。可在 SQLite / DB Browser for SQLite 中逐条运行。
PRAGMA foreign_keys = ON;

-- 1. 所有火元素角色及其武器类型。
SELECT name_zh AS 角色, element AS 元素, weapon AS 武器, rarity AS 星级
FROM characters WHERE element = '火' ORDER BY rarity DESC, name_zh;

-- 2. 香菱从 0 到 6 阶突破的所有材料总需求：JOIN + SUM + GROUP BY。
SELECT c.name_zh AS 角色, m.name_zh AS 材料, SUM(r.quantity) AS 总需求
FROM ascension_requirements r
JOIN characters c ON c.id = r.character_id
JOIN materials m ON m.id = r.material_id
WHERE c.slug = 'xiangling' AND r.phase BETWEEN 1 AND 6
GROUP BY c.id, m.id ORDER BY 总需求 DESC;

-- 3. 某种材料被多少位角色使用：多对多关联表。
SELECT m.name_zh AS 材料, COUNT(DISTINCT r.character_id) AS 使用角色数
FROM ascension_requirements r
JOIN materials m ON m.id = r.material_id
GROUP BY m.id ORDER BY 使用角色数 DESC LIMIT 10;

-- 4. 香菱全部突破阶段所需材料 vs 背包，计算缺口。
WITH needs AS (
    SELECT material_id, SUM(quantity) AS required
    FROM ascension_requirements
    WHERE character_id = (SELECT id FROM characters WHERE slug='xiangling')
    GROUP BY material_id
)
SELECT m.name_zh, n.required AS 总需求,
       COALESCE(i.quantity, 0) AS 背包已有,
       MAX(0, n.required - COALESCE(i.quantity, 0)) AS 仍缺
FROM needs n JOIN materials m ON m.id=n.material_id
LEFT JOIN inventory i ON i.material_id=n.material_id
ORDER BY 仍缺 DESC;

-- 5. 外键验证：如果尝试新增一个角色 ID 不存在的需求，会报 FOREIGN KEY constraint failed。
-- 请不要在课堂现场的正式库执行未注释的破坏性测试；可在临时副本中运行。
-- INSERT INTO ascension_requirements(character_id,phase,material_id,quantity)
-- VALUES(999999999,1,202,100);
