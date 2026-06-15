# OpenClaw PR — 提交流程

## 前置准备

```bash
# 1. Fork https://github.com/OpenClaw/OpenClaw

# 2. Clone + 切分支
git clone git@github.com:<小号>/OpenClaw.git
cd OpenClaw
git checkout -b feat/openclaw-error-handler

# 3. 安装依赖
pnpm install

# 4. 改文件
# 编辑 src/infra/fatal-error-hooks.ts:
#   - 顶部加 import { spawn } from "node:child_process";
#   - 文件末尾加 runExternalErrorHandler() 函数
#   - 在 runFatalErrorHooks() 末尾加 runExternalErrorHandler(context);
```

## 代码改动

### `src/infra/fatal-error-hooks.ts`

顶部 import 区：
```typescript
import { spawn } from "node:child_process";
```

文件末尾：
```typescript
/**
 * If OPENCLAW_ERROR_HANDLER is set, spawns the executable with error context
 * as a single JSON argument. The handler must be a path to an executable
 * (not a shell command) — shell expansion is deliberately disabled.
 *
 * Security: shell:false prevents command injection via environment variable.
 * The handler runs detached; OpenClaw does not wait for its completion.
 */
function runExternalErrorHandler(context: FatalErrorHookContext): void {
  const handler = process.env.OPENCLAW_ERROR_HANDLER?.trim();
  if (!handler) return;

  try {
    const payload = JSON.stringify({
      schemaVersion: 1,
      reason: context.reason,
      name: context.error instanceof Error ? context.error.name : undefined,
      message: context.error instanceof Error ? context.error.message : undefined,
      stack: context.error instanceof Error ? context.error.stack?.split("\n").slice(0, 6).join("\n") : undefined,
      timestamp: new Date().toISOString(),
      pid: process.pid,
    });

    const child = spawn(handler, [payload], {
      stdio: ["ignore", "inherit", "inherit"],
      detached: true,
      shell: false,
    });

    child.on("error", () => {
      // Async spawn error (ENOENT etc.) — silently ignored, must not race or crash the main process.
    });
    child.unref();
  } catch (err) {
    console.error("[fatal-error-hooks] OPENCLAW_ERROR_HANDLER failed:", String(err));
  }
}
```

在 `runFatalErrorHooks()` 函数末尾，`return messages;` 之前加：
```typescript
  runExternalErrorHandler(context);
```

## 编译 + 测试

```bash
# 5. 编译
pnpm build

# 6. 测试三种场景，截取终端输出

# 场景1 — 无 env var
node dist/index.js --version

# 场景2 — 正常 handler
OPENCLAW_ERROR_HANDLER="/usr/bin/logger" node dist/index.js --version

# 场景3 — 坏 handler
OPENCLAW_ERROR_HANDLER="/nonexistent" node dist/index.js --version
```

把三条命令的实际输出贴进 PR 的 **Real behavior proof** 段。

## 提 PR

```bash
git add src/infra/fatal-error-hooks.ts
git commit -m "feat(infra): add structured custom error handler via OPENCLAW_ERROR_HANDLER"
git push origin feat/openclaw-error-handler
```

在 GitHub 创建 PR：
- **Title:** `feat(infra): Add structured custom error handler via OPENCLAW_ERROR_HANDLER`
- **Body:** 复制 `PR_BODY.md` 全文，把 Testing 段的实际输出替换进去

---

## 红线 (DO NOT CROSS)

- ❌ 正文不出现 MisakaNet
- ❌ 不等待 handler 退出（`detached: true` + `child.unref()`）
- ❌ handler 失败不抛异常（空 `catch` 改为 `console.error` 但不要 `process.exit`）
- ❌ `shell: false` 绝不要改成 `shell: true`
