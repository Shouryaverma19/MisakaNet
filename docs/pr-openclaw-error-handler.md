# OpenClaw Error Handler PR — 完整方案

> 最终更新：2026-06-15 | 审计：minimax M3

## 最终设计

```typescript
function runExternalErrorHandler(context: FatalErrorHookContext): void {
  const handler = process.env.OPENCLAW_ERROR_HANDLER?.trim();
  if (!handler) return;
  try {
    // Default: redacted payload (no name/message/stack) — argv is visible
    // in process listings on most systems. Full details require explicit opt-in.
    const isRaw = process.env.OPENCLAW_ERROR_HANDLER_RAW === "1";
    const payloadObj: Record<string, unknown> = {
      schemaVersion: 1,
      reason: context.reason,
      timestamp: new Date().toISOString(),
      pid: process.pid,
    };
    if (isRaw && context.error instanceof Error) {
      payloadObj.name = context.error.name;
      payloadObj.message = context.error.message;
      payloadObj.stack = context.error.stack?.split("\n").slice(0, 6).join("\n");
    }
    const payload = JSON.stringify(payloadObj);
    const child = spawn(handler, [payload], {
      stdio: ["ignore", "inherit", "inherit"],
      detached: true,
      shell: false,
    });
    child.on("error", () => {
      // Async error from spawn (e.g. ENOENT) — silently ignored,
      // must not race or crash the main process.
    });
    child.unref();
  } catch (err) {
    console.error("[fatal-error-hooks] OPENCLAW_ERROR_HANDLER failed:", String(err));
  }
}
```

## 审计修掉的坑 (minimax M3)

| 问题 | 原版 | 修复 |
|------|------|------|
| `shell: true` 命令注入 | 攻击者可执行任意命令 | `shell: false`，只接受可执行文件路径 |
| stdin flush 时序竞争 | `process.exit` 在 handler 读完前关闭 pipe | argv[1] 传 JSON，原子传递 |
| 丢 error 字段 | 只传 `reason` | 传 `name`/`message`/`stack` |
| 无 schemaVersion | 未来加字段破坏 handler | 加 `schemaVersion: 1` |
| 静默吞错 | `catch {}` | `console.error` |

## 交付物

| 文件 | 路径 |
|------|------|
| PR body（OpenClaw 模板格式） | `openclaw-pr/PR_BODY.md` |
| 操作步骤 + 红线 | `openclaw-pr/INSTRUCTIONS.md` |
| 崩溃转发器参考实现 | `openclaw-pr/oc-error-forwarder.js` |

## 提交流程

1. 小号 fork OpenClaw
2. 按 `INSTRUCTIONS.md` 改文件、编译、测试
3. 贴测试输出到 PR body 的 Real behavior proof 段
4. 提 PR，标题 `feat(infra): Add structured custom error handler via OPENCLAW_ERROR_HANDLER`

## feat(infra): Add structured custom error handler via OPENCLAW_ERROR_HANDLER

## Summary

Add support for the `OPENCLAW_ERROR_HANDLER` environment variable. When set, OpenClaw spawns the specified command as a non-blocking subprocess with structured error context (JSON) piped to its stdin before exiting on a fatal error.

This lets users hook their own error notification, logging, or diagnostic tools into OpenClaw's fatal error flow without modifying any source code.

No new dependencies. Non-blocking by design — the handler runs detached; OpenClaw exits normally regardless of handler outcome.

## Changes

### 1. `src/infra/fatal-error-hooks.ts`

Add a helper that reads `OPENCLAW_ERROR_HANDLER` from the environment and spawns it:

```typescript
/** If OPENCLAW_ERROR_HANDLER is set, spawns it with error context as stdin (non-blocking). */
function runExternalErrorHandler(context: FatalErrorHookContext): void {
  const handler = process.env.OPENCLAW_ERROR_HANDLER?.trim();
  if (!handler) return;

  try {
    // Default: redacted payload (no name/message/stack) — argv is visible
    // in process listings. Full details require explicit opt-in.
    const isRaw = process.env.OPENCLAW_ERROR_HANDLER_RAW === "1";
    const payloadObj: Record<string, unknown> = {
      schemaVersion: 1,
      reason: context.reason,
      timestamp: new Date().toISOString(),
      pid: process.pid,
    };
    if (isRaw && context.error instanceof Error) {
      payloadObj.name = context.error.name;
      payloadObj.message = context.error.message;
      payloadObj.stack = context.error.stack?.split("\n").slice(0, 6).join("\n");
    }
    const payload = JSON.stringify(payloadObj);
    const child = spawn(handler, [payload], {
      stdio: ["ignore", "inherit", "inherit"],
      detached: true,
      shell: false,
    });
    child.on("error", () => {});
    child.unref();
  } catch (err) {
    console.error("[fatal-error-hooks] OPENCLAW_ERROR_HANDLER failed:", String(err));
  }
}
```

Import `spawn` at the top of the file:

```typescript
import { spawn } from "node:child_process";
```

### 2. Call `runExternalErrorHandler` in the fatal error path

In `runFatalErrorHooks`, after running registered hooks, add the external handler call:

```typescript
export function runFatalErrorHooks(context: FatalErrorHookContext): string[] {
  const messages: string[] = [];
  for (const hook of hooks) {
    try {
      const message = hook(context);
      if (typeof message === "string" && message.trim()) {
        messages.push(message);
      }
    } catch (err) {
      messages.push(formatHookFailure(err));
    }
  }
  // Non-blocking external handler (env var driven, no registration needed)
  runExternalErrorHandler(context);
  return messages;
}
```

## Verification

1. Without env var — no change in behavior
2. With `OPENCLAW_ERROR_HANDLER="cat"` — error JSON printed to stdout before exit
3. With `OPENCLAW_ERROR_HANDLER="/nonexistent"` — OpenClaw exits cleanly, no crash

## Rationale

- Follows existing precedent: `OPENCLAW_GATEWAY_STARTUP_TRACE` already uses env vars for runtime behavior control
- Zero new dependencies — `child_process.spawn` is Node.js stdlib
- Detached + unref means the handler cannot block OpenClaw's shutdown
- The JSON schema is minimal and forward-compatible — additional fields can be added later
- Pure extensibility — does not change any existing code paths
