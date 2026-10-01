// glossary-data.js —— 术语六层数据（F45 · ADR-0026）
// 结构：term/term_en/correct/metaphor/like/unlike/views/links
// 门闸：tools/dev/term-check.py（T1–T8；硬约束 len(unlike) ≥ len(like)）
// 比喻来源：tools/dev/series-metaphors.json（十篇连载 50 组提炼，禁现编）
// 渲染：reference/index.html 数据驱动改造时接入（P1 试点 10 条，待填）
const GLOSSARY = [];
