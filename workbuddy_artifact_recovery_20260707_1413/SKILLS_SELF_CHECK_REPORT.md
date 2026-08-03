# SKILLS_SELF_CHECK_REPORT.md

> **WorkBuddy Skills Self-Check Report**
> Generated: 2026-07-07T14:33+08:00
> Scope: Read-only audit of all skill/tool installations across user and project directories

---

## 1. Answer to Key Questions

### Q1: `.workbuddy/skills/` (project) 是否为空？

**Answer: YES — 项目级 `.workbuddy/skills/` 目录不存在或为空。**

```
C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\.workbuddy\skills/ → NOT FOUND or EMPTY
```

### Q2: 是否在其他目录发现 skill？

**Answer: YES — 在以下目录发现 skills：**

| Location | Skills Found | Type |
|----------|--------------|------|
| `~/.workbuddy/skills/` | 95+ skills | User-level WorkBuddy skills |
| `~/.claude/skills/` | 95+ symlinks | Claude skills (symlinks to `.agents/skills/`) |
| `~/.agents/skills/` | 95+ skills | Agent skills (shared source) |
| `~/.codex/skills/.system/` | 5 system skills | Codex system skills |
| `~/.config/devin/skills/` | 95+ skills | Devin skills |
| `~/.config/goose/skills/` | 95+ skills | Goose skills |

### Q3: 是否发现 Codex / Claude / agent skill？

**Answer: YES — 三种类型的 skill 都存在：**

1. **Codex system skills**: `~/.codex/skills/.system/` (imagegen, openai-docs, plugin-creator, skill-creator, skill-installer)
2. **Claude skills**: `~/.claude/skills/` (symlinks to `.agents/skills/`)
3. **Agent skills**: `~/.agents/skills/` (95+ ecommerce skills)

### Q4: 是否发现 `npx skills add` 安装痕迹？

**Answer: 无法确认。** 命令历史不可直接访问（Bash history 和 PowerShell history 都无法安全读取）。但从文件结构看，skills 是通过 WorkBuddy 内置的 skill marketplace 安装的，不是通过 `npx skills add`。

### Q5: 是否发现 gosom/google-maps-scraper？

**Answer: YES — 发现两种形式：**

1. **Go binary**: `tools/google-maps-scraper/gmaps-scraper.exe` (59MB, PE32+ Windows executable)
   - 来源: `github.com/gosom/google-maps-scraper`
   - 类型: 独立 Go 二进制文件
   - 状态: 可用，但之前测试失败 ("unexpected page type")

2. **Python Playwright POC**: `tools/google-maps-scraper/gmaps_fast_poc.py` (8KB)
   - 来源: 项目自建
   - 类型: Python 脚本，使用 Playwright
   - 状态: 可用，已成功运行

### Q6: 它是 skill、源码、exe、还是普通工具？

**Answer: 普通工具（不是 skill）。**

- `gmaps-scraper.exe` 是下载的 Go 二进制文件，不是 WorkBuddy skill
- `gmaps_fast_poc.py` 是项目自建的 Python 脚本，不是 skill
- 没有 `SKILL.md`、`skill.json`、或任何 skill manifest 指向 Google Maps scraper
- 这些工具只是放在 `tools/` 目录下的普通文件

### Q7: 是否发现 Crawlee / Scrapy / browser-use 等工具？

**Answer: 部分发现。**

| Tool | Status | Location |
|------|--------|----------|
| **Playwright** | ✅ 已安装 | `pip list` shows `playwright 1.60.0` |
| **Playwright browsers** | ✅ 已安装 | `~/.local/share/ms-playwright/` (chromium-1200, chromium-1223) |
| **BeautifulSoup** | ✅ 已安装 | `pip list` shows `beautifulsoup4 4.15.0` |
| **httpx** | ✅ 已安装 | `pip list` shows `httpx 0.28.1` |
| **Crawlee** | ❌ 未安装 | Not found in pip list or any directory |
| **Scrapy** | ❌ 未安装 | Not found in pip list or any directory |
| **browser-use** | ❌ 未安装 | Not found in any directory |
| **Selenium** | ❌ 未安装 | Not found in pip list |

### Q8: 是否发现 Google Maps 相关脚本？

**Answer: YES — 发现以下文件：**

| File | Path | Size | Purpose |
|------|------|------|---------|
| `gmaps-scraper.exe` | `tools/google-maps-scraper/` | 59MB | Go binary scraper (gosom) |
| `gmaps_fast_poc.py` | `tools/google-maps-scraper/` | 8KB | Fast Playwright POC |
| `gmaps_playwright_poc.py` | `tools/google-maps-scraper/` | 12KB | Full Playwright POC |
| `inventory_shift_ar_ky.py` | `tools/google-maps-scraper/` | 9KB | AR/KY inventory shift |
| `inventory_shift_live.py` | `tools/google-maps-scraper/` | 8KB | Live inventory shift |
| `queries_tn.txt` | `tools/google-maps-scraper/` | 781B | TN search queries |
| `queries_test.txt` | `tools/google-maps-scraper/` | 50B | Test queries |
| `GOOGLE_MAPS_BRANCH_POC_REPORT.md` | workspace root | 3.7KB | POC report |
| `GOOGLE_MAPS_ANTI_SCRAPE_NOTE_CN.md` | workspace root | 2.9KB | Anti-scrape notes |
| `GOOGLE_MAPS_CANDIDATES_TN_SAMPLE.csv` | workspace root | 88KB | TN sample data |
| `MANUAL_CONTACT_FETCH_QUEUE.csv` | workspace root | 22KB | Manual contact queue |
| `MANUAL_CONTACT_FETCH_QUEUE_CN.md` | workspace root | 5.1KB | Queue description |
| `MANUAL_CONTACT_FETCH_TOP30_CN.md` | workspace root | 7.5KB | Top 30 details |

### Q9: 是否发现 `gmaps_fast_poc.py`？

**Answer: YES — 存在于 `tools/google-maps-scraper/gmaps_fast_poc.py`。**

- 大小: 8KB
- 依赖: `playwright.sync_api`
- 功能: 快速提取 Google Maps 搜索结果卡片（不抓取详情页）
- 已测试: 成功运行，238 个候选 → 217 个新独立商店

### Q10: 当前 Google Maps Branch 实际依赖哪个工具？

**Answer: 主要依赖 `gmaps_fast_poc.py`（Python Playwright）。**

| Tool | Used? | Result |
|------|-------|--------|
| `gmaps-scraper.exe` (gosom) | ❌ 测试失败 | "unexpected page type" error |
| `gmaps_fast_poc.py` (Playwright) | ✅ 成功 | 238 candidates, 217 new stores |
| `gmaps_playwright_poc.py` | ⚠️ 未测试 | 可能是完整版 |

### Q11: 之前所谓"skill"到底是什么？

**Answer: 以下是分类：**

| Item | Classification | Evidence |
|------|---------------|----------|
| **us-retail-lead-collector** | ✅ 已安装 skill | `~/.workbuddy/skills/us-retail-lead-collector/SKILL.md` exists, `agent_created: true`, `disable: true` |
| **imap-smtp-email** | ✅ 已安装 skill | `~/.workbuddy/skills/skill_2053082149365157888/SKILL.md` exists |
| **cn-ecommerce-search** | ✅ 已安装 skill | `~/.workbuddy/skills/skill_2054901281445961728/SKILL.md` exists |
| **ecommerce-copywriter** | ✅ 已安装 skill | `~/.workbuddy/skills/skill_2054901364493180928/SKILL.md` exists |
| **gmaps-scraper.exe** | ❌ 下载的工具 | Go binary, not a skill |
| **gmaps_fast_poc.py** | ❌ 项目脚本 | Python script, not a skill |
| **browser_verifier.py** | ❌ 项目脚本 | Python script, not a skill |
| **fast_lead_discovery.py** | ❌ 项目脚本 | Python script, not a skill |
| **daily_operator_auto.py** | ❌ 项目脚本 | Python script, not a skill |
| **95+ ecommerce skills** | ✅ 已安装 skills | Via WorkBuddy marketplace |

### Q12: 哪些工具建议保留？

**Answer:**

| Tool | Recommendation | Reason |
|------|---------------|--------|
| `us-retail-lead-collector` skill | ✅ 保留 | BD-specific, agent_created |
| `imap-smtp-email` skill | ✅ 保留 | IMAP/SMTP capability |
| `gmaps_fast_poc.py` | ✅ 保留 | 成功运行，快速候选发现 |
| `gmaps_playwright_poc.py` | ✅ 保留 | 完整版 Playwright POC |
| `inventory_shift_ar_ky.py` | ✅ 保留 | AR/KY 库存班次 |
| `inventory_shift_live.py` | ✅ 保留 | 实时库存班次 |
| `browser_verifier.py` | ✅ 保留 | Playwright 验证 |
| `fast_lead_discovery.py` | ✅ 保留 | 快速线索发现 |
| Playwright + Chromium | ✅ 保留 | 浏览器自动化基础 |
| BeautifulSoup + httpx | ✅ 保留 | HTTP 抓取基础 |

### Q13: 哪些工具不建议继续使用？

**Answer:**

| Tool | Recommendation | Reason |
|------|---------------|--------|
| `gmaps-scraper.exe` (gosom) | ⚠️ 不推荐 | 之前测试失败，"unexpected page type" |
| Crawlee | ❌ 未安装 | Windows 兼容性风险 |
| Scrapy | ❌ 未安装 | 未安装 |
| Selenium | ❌ 未安装 | Playwright 更好 |

### Q14: 是否需要补建 `PROJECT_SKILLS.md`？

**Answer: YES — 强烈建议。**

当前项目没有 `PROJECT_SKILLS.md`，导致：
1. Codex 无法找到项目实际能力
2. 工具散落在多个目录
3. 没有统一的能力清单

建议在项目根目录创建 `PROJECT_SKILLS.md`，记录所有实际可用能力。

---

## 2. Summary

### 2.1 Skills Found

| Category | Count | Status |
|----------|-------|--------|
| **WorkBuddy user-level skills** | 95+ | ✅ Installed |
| **Claude skills** | 95+ | ✅ Symlinks to .agents/skills |
| **Agent skills** | 95+ | ✅ Shared source |
| **Codex system skills** | 5 | ✅ System |
| **Devin skills** | 95+ | ✅ Symlinks |
| **Goose skills** | 95+ | ✅ Symlinks |
| **BD-specific skills** | 1 | ✅ us-retail-lead-collector |
| **IMAP/SMTP skills** | 1 | ✅ imap-smtp-email |
| **Google Maps tools** | 6 | ⚠️ Not skills, just scripts/binary |

### 2.2 Key Findings

1. **`.workbuddy/skills/` (project) is EMPTY** — no project-level skills
2. **User-level `.workbuddy/skills/` has 95+ skills** — mostly ecommerce
3. **Only 1 BD-specific skill found**: `us-retail-lead-collector` (disabled)
4. **Google Maps tools are NOT skills** — they are plain scripts/binary
5. **`gmaps-scraper.exe` failed** — use `gmaps_fast_poc.py` instead
6. **Playwright is installed** — with Chromium browsers
7. **No Crawlee/Scrapy/browser-use** — not installed
8. **No `PROJECT_SKILLS.md`** — needs to be created

### 2.3 Recommendations

1. **Create `PROJECT_SKILLS.md`** — document all actual capabilities
2. **Enable `us-retail-lead-collector` skill** — currently disabled
3. **Use `gmaps_fast_poc.py`** — not `gmaps-scraper.exe`
4. **Consider installing Crawlee** — if faster crawling needed
5. **Document tool locations** — for Codex reference
