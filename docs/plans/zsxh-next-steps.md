# zsxh 小号执行计划

> 生成: 2026-06-18 | OpenClaw ✅ → Playwright 🎯

---

## Phase 1: OpenClaw PR 后台监控

- PR #93310: 所有检查绿 ✅ 金虾
- 等 maintainer 点 approve
- 不再主动投入

---

## Phase 2: Playwright — 主攻 🎯

**仓库**: `microsoft/playwright`
**入口**: `packages/playwright-core/src/cli/program.ts`

```
cliProgram().catch(logErrorAndExit)
  → gracefullyProcessExitDoNotHang(1)
```

**收口点**: `logErrorAndExit(e: Error)` 函数 + `.catch()` 链

| 维度 | 值 |
|------|-----|
| 语言 | TypeScript |
| 收口 | `logErrorAndExit` 全局函数 + 多处 `.catch()` |
| 目标改动 | ~15 行注入 `PLAYWRIGHT_ERROR_HANDLER` |
| 环境变量 | `PLAYWRIGHT_ERROR_HANDLER` |
| 难度 | ⭐⭐（比 tsdown 多几个 catch 链）|

### 动作清单

```
1. fork microsoft/playwright
2. 找 logErrorAndExit → 在调用前注入 env handler
3. 改 + build + 真 fatal path proof
4. PR body（OpenClaw v6 模板改 Playwright 版）
5. commit + signoff + push
6. @botname re-review
```

---

## Phase 3: E2B — 侦察 🔍

**仓库**: `e2b-dev/desktop` 或 `e2b-dev/cli`

### 侦察清单

```
1. 找 package.json → bin 字段 → CLI 入口
2. 找 process.on('uncaughtException') / try...catch 顶层收口
3. 评估是否适合 _ERROR_HANDLER 模式
```

---

## Phase 4: tsdown + Vite 跟进

- tsdown PR #1 — 等 ClawSweeper/Codex review
- Vite — 侦查完成，catch 块定位完毕，待命

---

## 红线（所有目标通用）

`shell:false` | `env:{PATH}` | `stdio:ignore` | `detached` | `unref` | 4 字段 payload
