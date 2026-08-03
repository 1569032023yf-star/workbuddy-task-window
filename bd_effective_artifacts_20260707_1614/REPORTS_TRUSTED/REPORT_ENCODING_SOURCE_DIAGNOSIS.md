# Report Encoding Source Diagnosis / 报告编码来源诊断

**Date / 日期**: 2026-07-07 15:51 Asia/Shanghai

---

## 1. 中文乱码出现阶段

**结论：乱码发生在 Codex/PowerShell 读取阶段，不是 WorkBuddy 生成阶段。**

原始文件在 WorkBuddy 中使用 `file` 命令检测结果为：

```
Unicode text, UTF-8 text, with very long lines (385), with CRLF line terminators
```

文件本身是合法的 UTF-8 编码，中文内容完整可读。

---

## 2. 原始文件编码

| 文件 | 编码 | 行尾 |
|------|------|------|
| FAST_INVENTORY_EXPANSION_TOOL_PLAN.md | UTF-8 | CRLF |
| FAST_INVENTORY_EXPANSION_EXECUTION_REPORT.md | UTF-8 | CRLF |
| STRICT_SENDABLE_POOL_AFTER_EXPANSION.md | UTF-8 | CRLF |
| LEAD_POOL_RESCUE_BACKFILL_REPORT.md | UTF-8 | CRLF |

---

## 3. 是否存在 UTF-8 正常源文件

**是。** 所有 4 个原始文件都是 UTF-8 编码，中文内容完整。

---

## 4. 是否是 PowerShell GBK 输出导致

**很可能是。** Windows PowerShell 默认使用 GBK (CP936) 编码读取和输出文件。如果 Codex 通过 PowerShell 读取 UTF-8 文件而未指定编码，中文字符会被错误解码为 `????` 或乱码。

PowerShell 读取 UTF-8 文件的正确方式：
```powershell
Get-Content -Path "file.md" -Encoding UTF8
```

如果使用 `Get-Content` 不带 `-Encoding UTF8`，PowerShell 会使用系统默认编码（Windows 中文版为 GBK），导致 UTF-8 中文被错误解码。

---

## 5. 是否是 Python 写文件未指定 encoding

**不是。** WorkBuddy 生成报告时使用 Python 的 `open()` 函数，默认编码为 UTF-8（在现代 Python 中），且文件经验证为合法 UTF-8。

---

## 6. 是否可以恢复原始中文

**可以。** 原始文件为 UTF-8 编码，中文内容完整。本次重导出已将原始文件复制为 UTF-8 with BOM (UTF-8-SIG) 格式，确保 Windows 工具能正确识别编码。

---

## 7. 哪些报告是原始恢复版

| 文件 | 版本 |
|------|------|
| FAST_INVENTORY_EXPANSION_TOOL_PLAN_UTF8.md | 原始恢复（UTF-8 → UTF-8-SIG） |
| FAST_INVENTORY_EXPANSION_EXECUTION_REPORT_UTF8.md | 原始恢复（UTF-8 → UTF-8-SIG） |
| STRICT_SENDABLE_POOL_AFTER_EXPANSION_UTF8.md | 原始恢复（UTF-8 → UTF-8-SIG） |
| LEAD_POOL_RESCUE_BACKFILL_REPORT_UTF8.md | 原始恢复（UTF-8 → UTF-8-SIG） |

---

## 8. 哪些报告是事实重建版

**无。** 所有 4 个报告都是原始恢复版，不是事实重建版。原始文件编码正确，中文内容完整。

---

## 9. 后续如何避免再次乱码

### 方案 A：使用 UTF-8 with BOM（推荐）

在 Python 写文件时使用 `encoding='utf-8-sig'`：
```python
with open('report.md', 'w', encoding='utf-8-sig') as f:
    f.write(content)
```

BOM (Byte Order Mark) 是文件开头的特殊字节 `EF BB BF`，Windows 工具会自动识别为 UTF-8。

### 方案 B：PowerShell 读取时指定编码

在 PowerShell 中读取文件时：
```powershell
Get-Content -Path "file.md" -Encoding UTF8
```

### 方案 C：使用 Git Bash / WSL

Git Bash 和 WSL 默认使用 UTF-8，不会出现编码问题。

### 方案 D：设置 PowerShell 默认编码

在 PowerShell 配置文件中添加：
```powershell
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
```

---

## 10. 总结

| 项目 | 结论 |
|------|------|
| 乱码阶段 | Codex/PowerShell 读取阶段 |
| 原始编码 | UTF-8 |
| 源文件完整 | 是 |
| PowerShell GBK | 很可能是原因 |
| Python 未指定 encoding | 否 |
| 可否恢复 | 可以（已恢复） |
| 恢复版数量 | 4 |
| 重建版数量 | 0 |
| 避免方案 | UTF-8-SIG (BOM) 或 PowerShell -Encoding UTF8 |

---

## 文件清单

| 输出文件 | 说明 |
|----------|------|
| FAST_INVENTORY_EXPANSION_TOOL_PLAN_UTF8.md | 原始恢复，UTF-8 with BOM |
| FAST_INVENTORY_EXPANSION_EXECUTION_REPORT_UTF8.md | 原始恢复，UTF-8 with BOM |
| STRICT_SENDABLE_POOL_AFTER_EXPANSION_UTF8.md | 原始恢复，UTF-8 with BOM |
| LEAD_POOL_RESCUE_BACKFILL_REPORT_UTF8.md | 原始恢复，UTF-8 with BOM |
| REPORT_ENCODING_SOURCE_DIAGNOSIS.md | 本诊断报告 |
