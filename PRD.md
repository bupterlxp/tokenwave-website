# TokenWave.ai 官网 PRD

- **版本**：v1.0（已定稿）
- **日期**：2026-07-17
- **状态**：四项待决问题已拍板，进入排期执行
- **参考站**：unipat.ai（模板/气质）、steven47521.github.io/Paper_visualization_v2（内容/数据）

---

## 0. 决策记录

| # | 问题 | 决策 | 日期 |
|---|---|---|---|
| D1 | 详情页范围 | **先做有榜单数据的 10~15 个**，其余二期 | 2026-07-17 |
| D2 | 粒子特效技术栈 | **保留 three.js**（669KB），暂不重写 | 2026-07-17 |
| D3 | Blog 文章正文页 | **需要**，本期实现 | 2026-07-17 |
| D4 | Compare 模型对比页 | **本期实现** | 2026-07-17 |

---

## 1. 背景与目标

TokenWave.ai 是公司对外的 benchmark 门户：以极简、可信、研究导向的形象，展示公司在
Agent / MLLM / AIGC / LLM 四个领域的 48 个 benchmark 及其榜单结果。

当前站点为 unipat.ai 的 1:1 模板复刻（原版 CSS、three.js 粒子特效、页面过渡状态机），
内容取自 Benchmark Hub 的目录数据，仅 SWE-Compass 有完整详情页。

### 本期核心目标

1. **内容完备**：有榜单数据的 benchmark（预估 10~15 个）拥有结构一致的详情页；Blog 有可读的文章正文；新增 Compare 模型对比页；
2. **风格差异化**：保留交互骨架，替换所有"一眼认出 unipat"的表层签名，达到"同类审美、不同签名"。

### 非目标（本期不做）

- 无榜单数据的 benchmark 详情页（列表索引仍展示全部 48 条，无详情页的条目跳分组锚点）；
- 后台 CMS / 数据库（维持纯静态站，数据以仓库内 JSON 管理）;
- 多语言（中文版后续单独立项）；
- 榜单在线提交入口；
- 粒子特效重写为 canvas 2D（D2 已决策保留 three.js，性能优化列观察项）。

---

## 2. 现状盘点

| 模块 | 状态 |
|---|---|
| 首页（打字机使命宣言 + 词典条） | ✅ 完成 |
| Benchmarks 列表页 | ✅ 完成（7 个精选卡片；缺全量 48 条索引入口） |
| Blog 列表页 | ✅ 完成（8 篇，摘要为占位文案，无正文页） |
| Join Us | ✅ 完成 |
| Benchmark 详情页 | ⚠️ 仅 SWE-Compass 1/48 |
| Compare 页 | ❌ 未建 |
| 卡片配图 | ⚠️ 自绘"论文插图风"SVG 8 张（arxiv.org 被内网拦截，原图未获取） |
| 粒子特效 / 页面过渡 | ✅ 原版移植，聚合形状已改为 TokenWave 文字 + 公司 logo |
| 风格 | ⚠️ 与 unipat 高度雷同（本期需差异化） |

**已验证的网络可达性**：unipat.ai ✅ / cdn.unipat.ai ✅ / steven47521.github.io ✅ /
arxiv.org ❌（拦截）/ fonts.googleapis.com 未依赖（字体已自托管）。

---

## 3. 工作流一：Benchmark 详情页（D1：榜单子集）

### 3.1 范围圈定

- **入选标准**：源站详情页 Leaderboard 表格有 ≥1 行模型数据（"Models scored ≥ 1"）；
- 圈定动作为 M1 第一步：脚本遍历 48 个 slug 抓取判定，输出入选清单供确认；
- 预估 10~15 个；若实际超过 15 个，按「榜单行数 × 域覆盖均衡」排序取前 15。

### 3.2 数据管线（脚本化，禁止手改 HTML）

```
tools/
  scrape.py        # 遍历源站 slug → data/benchmarks/<slug>.json
  build.py         # JSON + 模板 → benchmarks/<slug>.html、列表页卡片、Blog 素材、Compare 数据
data/
  benchmarks/<slug>.json   # 单一事实来源
  compare.json             # build.py 汇总生成：模型 × benchmark 分数矩阵
```

**JSON Schema（v1）**：

```json
{
  "slug": "swe_compass",
  "name": "SWE-Compass",
  "domain": "agent",              // agent | multimodal | aigc | llm
  "subcategory": "Code Agent",
  "abstract": "...",
  "contributions": ["..."],
  "method": ["..."],
  "metrics": [{"name": "AVG", "direction": "higher", "range": "[0, 100]", "note": "..."}],
  "leaderboard": [{"rank": 1, "model": "Claude Sonnet 4", "score": 32.9, "source": "Official", "date": null}],
  "at_a_glance": {"focus": "...", "primary_metric": "AVG", "setting": "...", "models_scored": 5, "data_updated": "2026-04-15"},
  "links": {"paper": null, "code": null},   // 源站有则抓，无则 null
  "image": "static/images/benchmarks/swe-compass.svg"
}
```

### 3.3 详情页模板

以现有 `benchmarks/swe-compass.html` 为基准模板（unipat detail 结构：detail-hero +
衬线 markdown 正文），字段映射见 Schema；无榜单字段的区块不渲染。
🏆 meta 行取 leaderboard[0]；列表页精选卡片同步从 JSON 生成。

### 3.4 配图策略（优先级从高到低）

1. arXiv 论文首页/teaser 渲染 PNG —— **依赖 arxiv.org、export.arxiv.org 加白**（风险 R1）；
2. benchmark GitHub 仓库官方 logo（如有，需逐个人工确认链接）；
3. 自绘"论文插图风"SVG 兜底（已有 8 张，入选清单内缺口在 M1 补齐；文件名 = slug，
   后续换真图只替换文件不改页面）。

### 3.5 验收标准

- 入选清单内详情页 100% 可访问、字段完整（无数据字段明确不渲染而非留空）；
- 列表页全量索引：有详情页的条目可点击进入，其余显示为不可点的普通标签（视觉区分）；
- `python3 tools/build.py` 幂等：重跑输出零 diff（数据未变时）。

---

## 4. 工作流二：Blog 文章正文页（D3）

### 4.1 信息架构

```
blog.html            # 列表页（现有）
blog/<slug>.html     # 文章正文页，新增
```

### 4.2 内容策略

> unipat 的做法（见附录 A.4）：文章正文页复用 benchmark 详情模板（detail-hero + 衬线 markdown），
> 但每篇文章内嵌一套**独立前缀的 scoped 样式**（如 `bv-`、`sb-`），包含浮动目录、交互式示例卡片、
> 文中榜单等富组件——文章即产品页。本期先实现基础正文（下述骨架），富组件模式列为文章升级方向。

- 每篇文章绑定一个 benchmark，正文从对应 JSON 组装骨架：引言（摘要改写）→ 为什么做
  （contributions）→ 方法（method）→ 主要结果（leaderboard 前 3 + 一句解读）→ 结语
  （指向详情页的 CTA）；
- 骨架生成后**人工润色一轮**再上线（避免 8 篇文章结构口吻完全一致）；
- 文章页模板复用 unipat detail 的 `.markdown` 衬线正文样式，头部为：日期 + 域标签 +
  标题 + 配图（与 benchmark 同图）；
- 列表页摘要与正文首段保持一致（由 build.py 保证）。

### 4.3 范围与验收

- 首批 8 篇（现有列表条目）全部有正文页，列表卡片点击进入正文而非跳 benchmarks 锚点；
- 正文内链：文章 → benchmark 详情页；详情页 → 相关文章（如有）。

---

## 5. 工作流三：Compare 模型对比页（D4）

### 5.1 源站功能基线（已调研）

源站 Compare 页为纯前端组件："Select up to 5 models for cross-benchmark comparison"
—— 选择最多 5 个模型，展示跨 benchmark 的分数对比。

### 5.2 本站需求

- **入口**：导航新增 Compare（Home / Blog / Benchmarks / Compare / Join Us）；
- **数据**：`data/compare.json`（build.py 从各 benchmark 的 leaderboard 汇总：
  模型名归一化 → 模型 × benchmark 分数矩阵）；
- **交互**（纯前端 JS，无依赖）：
  1. 模型多选（上限 5，超出禁用），按出现的 benchmark 数排序展示候选；
  2. 对比表格：行 = benchmark（含域标签与主指标名），列 = 所选模型；每行最高分高亮；
  3. 空态：未选择时显示引导文案；模型在某 benchmark 无成绩显示 "–"；
- **不做**：雷达图/柱状图可视化（二期）、URL 状态分享（二期）；
- **风格**：遵循工作流四差异化后的视觉规范。

### 5.3 验收标准

- 任选 ≤5 模型，表格正确渲染全部有数据的 benchmark 行，最高分高亮无误；
- 模型名归一化规则有文档（如 "Claude-Opus-4.7" 与 "Claude Opus 4.7" 合并），
  归一化映射表在 data/ 下可人工修正。

---

## 6. 工作流四：风格差异化（去雷同）

**原则**：保留已验证的交互骨架（粒子背景、页面过渡、卡片列表结构），替换表层签名。
按辨识度排序，逐项可独立上线：

| 优先级 | 项目 | 现状（unipat 签名） | 差异化方案 |
|---|---|---|---|
| P0 | 正文字体 | 全站 Space Mono 等宽 | 标题/数据保留等宽点缀，正文换无衬线（系统栈或 IBM Plex Sans，需自托管） |
| P0 | 首页 Hero | 打字机逐字 + 闪烁光标 | 整句淡入 + 关键词底色扫过，或按词淡入；**弃用光标** |
| P0 | 粒子形态 | 灰度散点、聚字节奏 3.5s/8s | 粒子色板映射 logo 蓝紫渐变；调整聚合序列（如加入波浪形态）与节奏参数 |
| P1 | 词典词条 | dict-entry 排版 | 改为"定义带"：顶部品牌色细条 + 渐变词头（v3 方案可复用） |
| P1 | 配色 | 纯黑白 | 引入 logo 蓝 #3B82F6 为唯一点缀色（链接、激活态、榜单高亮、Compare 高亮） |
| P1 | 卡片 | 左图右文、10px 圆角、悬停浮起 | 保留结构，调整圆角/边框/阴影参数，图片改右置或加内边距留白 |
| P2 | 页脚 / 导航 | 居中单行 / 下划线激活 | 页脚左右分栏；导航激活改背景胶囊或小圆点 |
| P2 | 动效参数 | 卡片 rise 0.52s、过渡 0.35s 等 | 统一微调节奏，避免与 unipat 逐帧一致 |

**尺度标准**：第三方并排对比两站时，不应能指认任何一段相同的视觉元素
（字体组合、动效行为、排版参数、CSS/JS 原文）。差异化完成后，
CSS 与过渡脚本应为重写产物而非 unipat 原文件的注释版。

### 验收标准

- P0 三项落地后做并排截图评审（首页 / Blog / 详情页 三组对比图）；
- 全站视觉一致性走查：新增的 Compare 页与 Blog 正文页遵循同一套 token（颜色/圆角/间距变量）；
- 性能底线：首屏 JS ≤ 800KB（three.js 保留，观察项：若后续测速不达标再触发 D2 复议）。

---

## 7. 里程碑

| 阶段 | 内容 | 依赖 | 产出 |
|---|---|---|---|
| M1 | 榜单子集圈定 + 抓取/生成管线 + 入选详情页上线（SVG 配图兜底） | 无 | 入选清单、tools/、data/、10~15 个详情页 |
| M2 | Blog 正文页 8 篇 + Compare 页 | M1（数据管线） | blog/、compare.html、data/compare.json |
| M3 | 风格差异化 P0 + P1 | 无（可与 M1/M2 并行） | 重写后的 CSS/动效、并排评审记录 |
| M4 | arXiv 配图批量替换 + P2 细节 + 全站回归 | arxiv.org 加白；M1~M3 | 真图替换、5 类页面截图走查 |

> M3 完成前站点不对外发布（见 R2）。

---

## 8. 风险与依赖

| # | 风险/依赖 | 影响 | 缓解 |
|---|---|---|---|
| R1 | arxiv.org / export.arxiv.org 内网拦截 | 论文原图与元数据无法获取 | SVG 兜底不阻塞；申请加白后 M4 批量替换（文件名即 slug，零页面改动） |
| R2 | 当前 CSS/JS 为 unipat 原文件移植 | 提前公开有被识别套壳风险 | M3 完成前不对外；差异化后 CSS/JS 为重写产物 |
| R3 | 源站数据口径与引用授权 | 对外合规 | 正式发布前确认数据引用授权；论文图注明 arXiv 出处 |
| R4 | 源站（GitHub Pages）访问偶发超时 | 抓取管线不稳定 | scrape.py 带重试与本地缓存；数据落库后不依赖运行时访问 |
| R5 | 模型名跨 benchmark 不一致 | Compare 矩阵错并/漏并 | 归一化映射表人工可修正（5.3） |

---

## 9. 遗留的二期候选

- 其余 ~33 个无榜单 benchmark 的详情页；
- Compare 可视化（雷达图/柱状图）与 URL 状态分享；
- 中文版；
- 榜单提交入口；
- 粒子特效轻量化（视 M3 后性能数据决定是否复议 D2）；
- Blog 富组件升级（附录 A.4 的 scoped 样式系统 + 浮动目录 + 交互卡片）。

---

## 附录 A：unipat.ai 站点全量清单（2026-07-17 实测）

> 依据：sitemap.xml + 逐页抓取。作为复刻完整度与差异化改造的对照基线。

### A.1 页面清单（sitemap 共 19 页）

| 类型 | 页面 | 数量 | TokenWave 对应状态 |
|---|---|---|---|
| 主页面 | `/`、`/blog`、`/benchmarks`、`/joinus` | 4 | ✅ 已复刻 |
| Blog 正文 | `/blog/<slug>`（babyvision、echo、experteval、swe-vision、saas-bench、terminalx、unimath、uniscientist） | 8 | 🔲 本期 M2（D3） |
| Benchmark 详情 | `/benchmarks/<slug>`（babyvision、clawbench、echo、evocode-bench、monthlyswebench、roadmapbench、saas-bench） | 7 | ⚠️ 1/48 → 本期 M1 做榜单子集 |
| 站外 | echo.unipat.ai（Echo Leaderboard 独立子站） | 1 | ❌ 不做（对应二期 Compare 可视化方向） |

注意：unipat 自己也只给 7 个 benchmark 建了详情页（精选制），与 D1"先做子集"的决策一致。

### A.2 全局基础设施

| 项目 | unipat 实现 | TokenWave 状态 |
|---|---|---|
| 字体 | Space Mono 两字重，CDN 自托管 woff2 | ✅ 已自托管 |
| 静态资源 | 独立 CDN 域（cdn.unipat.ai）：css/js/fonts/images/favicon | ⚠️ 本地 static/，发布时再定 CDN |
| SEO | sitemap.xml（含 lastmod/changefreq）、robots.txt、每页 OG 卡片 + Twitter Card、og-default 分享图 | 🔲 M4 补齐 |
| Favicon | png 三尺寸（favicon / 192 / apple-touch-icon） | ⚠️ 现为单 SVG，M4 补多尺寸 |
| 统计 | Google Analytics，按 hostname 判断仅生产环境加载 | 🔲 待定统计方案（内网环境 GA 可能不可用） |
| 公式 | MathJax 3 全站挂载（tex 行内/块级），论文类文章会用到 | 🔲 M2 随 Blog 正文页引入 |
| 页脚 | 居中一行"UniPat AI · contact@" + X 图标外链 | ✅ 已复刻（X 链接待换公司账号） |

### A.3 特效与交互系统（复刻完成度）

| 特效 | unipat 行为细节 | TokenWave 状态 |
|---|---|---|
| 粒子背景 | three.js，4000 灰度粒子；状态机：散点 3.5s → "UniPat" 8s → 散点 3s → favicon logo 8s → 散点 3s → "AI" 8s 循环；五次方缓动 + 逐粒子随机延迟（0~38%）；鼠标斥力（半径 55、弹簧阻尼回弹）+ 相机视差；滚动 150~500px 渐隐 20%；手机端简化为 4 状态；跨页 sessionStorage 序列化粒子状态无缝续播；导航前冻结快照防闪 | ✅ 已复刻（文字/logo 已换）；M3 改色板与节奏 |
| 页面过渡 | 主页面间 fetch 软切换（换 main 不刷新），进出详情页整页淡出淡入；bfcache/popstate 恢复处理 | ✅ 已复刻 |
| 打字机 Hero | 22ms/字符逐字打出 + 闪烁光标（border-right 实现） | ✅ 已复刻；M3 P0 替换（去雷同） |
| 卡片入场 | rise 动画 0.52s cubic-bezier，逐张延迟 0.05~0.69s，等 cards-ready 才播放 | ✅ 已复刻；M3 P2 调参数 |
| 首帧防闪 | head 内联脚本：full 过渡到达时先把 html opacity 置 0 | ✅ 已复刻 |

### A.4 内容模式（对 M1/M2 的直接启示）

- **详情页模板**：`detail-hero`（左图 160px + eyebrow + h1 + muted meta 行）+ `.markdown` 衬线正文；
  benchmark 页 meta 行格式为「🏆 <模型>: <分数> · <分类>」，Blog 页 meta 行为日期；
- **文章即产品页**：每篇 Blog/benchmark 正文内嵌**独立前缀 scoped 样式**（BabyVision 用 `bv-`，
  SaaS-Bench 用 `sb-`，后者还是完整的 Mondrian 设计系统），包含：浮动目录（Notion 风）、
  hero 内链接按钮排（Paper/Code/Data）、统计格（sb-stats 四宫格）、文中完整榜单表、
  交互式 QA 示例卡、多模型输出对比网格——单页 HTML 可达 140KB；
- **图片规范**：全部走 CDN `static/images/<benchmark>/<file>`，卡片图 `background-size: contain`
  白底，详情 hero 图 `cover` 带边框；
- **列表页卡片 meta**：benchmark 卡为「🏆 榜首 · 分类」，blog 卡为日期——两处模板一致仅 meta 不同；
- **外链卡片**：列表中可混入外部站点条目（Echo Leaderboard `target="_blank"`），模板兼容。

### A.5 对照结论

1. 复刻完成度：主页面 4/4、特效 5/5、详情模板 1 套已就绪；缺口 = Blog 正文 0/8、
   benchmark 详情 1/7（对齐 unipat 精选制口径）、SEO 基础设施；
2. unipat 的"精选详情页 + 全量不建页"策略印证 D1 决策；
3. Blog 富组件（A.4）是 unipat 内容质感的主要来源，二期升级时优先级应高于 Compare 可视化。
