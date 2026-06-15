# OpenClaw Error Handler PR — 交付物

> 对应设计文档: `../pr-openclaw-error-handler.md`

## 决策总结

**设计方案**: C方案 — redact-by-default
**审计**: minimax M3 (已通过，所有阻塞问题已修复)
**状态**: ⏳ 待提 PR

### 已修定的关键问题 (minimax M3 audit)

| 问题 | 修复 |
|------|------|
| `shell: true` 命令注入 | → `shell: false`，只接受可执行文件路径 |
| stdin flush 时序竞争 | → argv[1] 传 JSON，原子传递 |
| 丢 error 字段 | → 传 `name`/`message`/`stack`(RAW=1 下) |
| 无 schemaVersion | → `schemaVersion: 1` |
| 静默吞错 | → catch 打 `console.error` |

### 文件索引

| 文件 | 说明 |
|------|------|
| `PR_BODY.md` | 最终版 PR 正文（可直接提交到 OpenClaw） |
| `INSTRUCTIONS.md` | 操作步骤 + 红线 |
| `INSTRUCTIONS.7z` | 加密版操作步骤 |
| `oc-error-forwarder.js` | 崩溃转发器参考实现（飞书/Local） |
| `proof.js` | 实机测试脚本（生成 Real behavior proof） |
| `PR_Gemini.md` | Gemini 原版（有 bug，仅存档参考） |
| `PR_minimax M3.md` | M3 审计报告（发现 7 个问题，2 个阻塞性） |

## 提交流程（下一步）

```bash
# 1. Fork https://github.com/OpenClaw/OpenClaw
# 2. 按 INSTRUCTIONS.md 改代码、编译、测试
# 3. 贴测试输出到 PR_BODY.md 的 Real behavior proof 段
# 4. 提 PR: feat(infra): Add structured custom error handler via OPENCLAW_ERROR_HANDLER
```

**红线**:
- ❌ 正文不出现 MisakaNet
- ❌ 不等待 handler 退出（`detached: true` + `child.unref()`）
- ❌ handler 失败不抛异常
- ❌ `shell: false` 绝不要改成 `shell: true`
