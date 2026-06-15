# feat(infra): Add structured custom error handler via OPENCLAW_ERROR_HANDLER

## Summary

This PR adds support for a universal `OPENCLAW_ERROR_HANDLER` environment variable. When defined, OpenClaw will automatically marshal fatal error diagnostic data into a structured JSON payload and pipe it to the specified command's `stdin` immediately before exiting.

This addresses a growing need for advanced observability and extensibility: it enables operators to seamlessly hook custom alerting (e.g., Webhooks, Discord/Slack notification scripts), specialized logging collectors, or local runtime recovery toolchains directly into OpenClaw’s lifecycle **without requiring custom plugins or underlying code modifications**.

### Design Considerations (Zero-Impact & Safe)
- **Zero Dependencies**: Relies exclusively on Node.js built-in `node:child_process`.
- **Non-Blocking & Detached**: The external process is spawned with `detached: true` and `child.unref()`. OpenClaw will shutdown normally and instantly, entirely independent of the handler's execution duration or output.
- **Fail-Safe Isolation**: Enclosed in a strict `try...catch` block; any runner or spawn failures are silently degraded to ensure OpenClaw's exit pathway remains perfectly deterministic.

## Changes

### 1. `src/infra/fatal-error-hooks.ts`

Add standard built-in import at the top:
```typescript
import { spawn } from "node:child_process";
Append the fail-safe runner at the end of the file:

TypeScript
/** If OPENCLAW_ERROR_HANDLER is set, spawns it with error context as stdin (non-blocking). */
function runExternalErrorHandler(context: FatalErrorHookContext): void {
  const handler = process.env.OPENCLAW_ERROR_HANDLER?.trim();
  if (!handler) return;

  try {
    const payload = JSON.stringify({
      reason: context.reason,
      timestamp: new Date().toISOString(),
      pid: process.pid,
    });

    const child = spawn(handler, [], {
      stdio: ["pipe", "inherit", "inherit"],
      detached: true,
      shell: true,
    });

    if (child.stdin) {
      child.stdin.write(payload);
      child.stdin.end();
    }
    child.unref();
  } catch {
    // Fail-safe: handler failure must never delay or crash main process termination
  }
}
2. Integration inside runFatalErrorHooks
Invoke the external router at the tail-end of runFatalErrorHooks() to capture the fully populated error context:

TypeScript
  // Non-blocking external handler (environment-driven fallback)
  runExternalErrorHandler(context);
Verification & Testing
Tested locally against the standard CLI runtime:

Without Env Var: Zero change in runtime behavior or memory footprint.

With Diagnostic Pipeline (OPENCLAW_ERROR_HANDLER="cat"): Properly dumps the structured JSON payload directly to terminal streams before clean exit.

With Dead Endpoint (OPENCLAW_ERROR_HANDLER="/usr/bin/nonexistent_file"): Gracefully degrades, ignores the invocation error, and terminates safely with no dangling references.

Rationale & Precedent
Aligns closely with current architectural patterns (e.g., OPENCLAW_GATEWAY_STARTUP_TRACE), which leverage clean environment variables to toggle granular runtime behavior.

Provides a generic, clean abstractions for any third-party ecosystem tool to integrate seamlessly with OpenClaw's diagnostic layer.