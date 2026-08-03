# PHASE 3: COLLECTION THROUGHPUT REPORT

**Date**: 2026-06-30 11:30  
**Mode**: Staging experiment (no production changes)

---

## 1. 是否安装 Crawlee Python

❌ **否** — Crawlee Python 在 Windows + Python 3.13 上兼容性风险较高，且依赖较重。

## 2. 如果没有安装，原因

- Crawlee Python 主要支持 Linux/macOS，Windows 支持有限
- 依赖 Playwright + Crawlee 双重框架，增加复杂度
- 现有 Playwright + httpx + BeautifulSoup 已足够实现分层逻辑

## 3. 是否使用 Crawlee-like 替代方案

✅ **是** — 使用 `httpx + BeautifulSoup + Playwright fallback` 实现 Crawlee-like 分层采集。

脚本：`roktandrazo-outreach/fast_lead_discovery.py`

## 4. 测试样本数量

| 测试 | 样本数 | 来源 |
|------|--------|------|
| B2 池测试 | 30 | B2 manual_review_needed（随机采样） |
| 已知好站测试 | 5 | 已确认有邮箱的门店 |

## 5. 总耗时

| 测试 | 总耗时 | 平均每条 |
|------|--------|----------|
| B2 池测试（30条） | 450s (7.5 min) | **15.0s** |
| 已知好站测试（5条） | 16.5s | **3.3s** |

## 6. 平均每条耗时

| 方法 | 平均耗时 | 速度倍数 |
|------|----------|----------|
| **Fast Discovery (HTTP-first)** | **3.3-15.0s** | **4-18x** |
| Browser Verifier (旧) | ~60s | 1x (基准) |

## 7. A0 新增数量

| 测试 | A0 |
|------|-----|
| B2 池测试 | 0（预期，B2 本就无可邮箱） |
| 已知好站测试 | 2（Noble Knight Games, Gamers Haunt） |

## 8. C 新增数量

| 测试 | C |
|------|---|
| B2 池测试 | 0 |
| 已知好站测试 | 0 |

## 9. B2 新增数量

| 测试 | B2 |
|------|-----|
| B2 池测试 | 30（预期） |
| 已知好站测试 | 3（Haunted Game Cafe, Phoenix Fire Games, Kidstop） |

## 10. Invalid 数量

0

## 11. verification_failed 数量

0

## 12. 是否发生真实发送

❌ **否**

## 13. 是否修改生产数据库

❌ **否** — 所有输出均为 JSON 文件，未写入数据库

## 14. 是否建议接入主流程

✅ **建议** — 但需要以下改进

## 15. 接入前还需要修什么

### 必须修复
1. **域名匹配逻辑** — 当前只匹配精确域名，需支持子域名（如 www.）
2. **Browser fallback 方法追踪** — 当前 `method` 字段在 browser fallback 时未正确更新
3. **反爬邮箱格式** — 需增加更多 obfuscated 模式支持（如 `info [at] domain.com`）

### 建议优化
1. **并发处理** — 当前是串行处理，可增加 3-5 并发
2. **资源屏蔽** — Browser fallback 已屏蔽图片/字体/视频，可进一步优化
3. **超时调优** — HTTP timeout 5s 对慢站可能不够，可增加到 8s
4. **域名去重** — 同一 domain 不重复验证

---

## 性能对比

| 指标 | Browser Verifier | Fast Discovery | 改善 |
|------|------------------|----------------|------|
| 平均耗时/条 | ~60s | 3.3-15s | **4-18x** |
| 30条处理时间 | ~30 min | 7.5 min | **4x** |
| 200条处理时间 | ~200 min (3.3h) | ~50 min | **4x** |
| 资源消耗 | 高（Playwright） | 低（HTTP为主） | **显著降低** |
| 邮箱发现率 | 高（JS渲染） | 中（纯HTTP） | 需配合 browser fallback |

## 架构建议

```
新线索 → HTTP 快筛 (5s) → 找到邮箱? → A0
                              ↓ 否
                    轻量页面发现 (3-5页)
                              ↓
                    找到邮箱? → A0
                              ↓ 否
                    Browser Fallback (8s)
                              ↓
                    找到邮箱? → A0
                              ↓ 否
                    Contact Form? → C
                              ↓ 否
                    B2 Manual Review
```

## 后续步骤

1. ✅ `fast_lead_discovery.py` 已创建并验证
2. 🔧 修复域名匹配和 method 追踪
3. 🔌 接入 `daily_operator_auto.py` 的 Lead Factory 流程
4. 🧪 对新城市线索批量测试（50-100条）
5. 📊 对比 Fast Discovery vs Browser Verifier 的 A0 发现率

---

*Generated at 2026-06-30 11:30*
