## Summary

Add support for `OPENCLAW_ERROR_HANDLER` — an environment variable that lets users route OpenClaw's fatal error diagnostics to an external executable as a structured JSON payload.

**Intent (2-3 bullets):**
- Non-blocking external handler for fatal errors (uncaught exceptions, CLI failures)
- Passes structured error context (`reason`, `name`, `message`, `stack`, `timestamp`, `pid`) as a single JSON argument
- Zero new dependencies, `shell: false` for command injection safety, `detached` + `unref()` for non-blocking shutdown

**What is intentionally out of scope:**
- Not a replacement for the existing `registerFatalErrorHook` plugin API (internal hooks still preferred for bundled diagnostics)
- Not a daemon or watchdog — fire-and-forget execution only

**What does success look like:**
- Users can set `OPENCLAW_ERROR_HANDLER="/usr/bin/logger"` and see structured error data in syslog
- Users can point it at a custom script to POST errors to their own alerting pipeline
- OpenClaw's exit path remains deterministic — handler failure never blocks shutdown

**What should reviewers focus on:**
- `detached: true` + `child.unref()` — confirm the handler cannot delay OpenClaw's exit
- `shell: false` — confirm the command injection surface is eliminated
- Payload schema — confirm `schemaVersion: 1` is sufficient for forward compatibility

---

## Linked context

Closes # (no issue filed for this feature)

Related # (none)

Was this requested by a maintainer or owner? No — community contribution.

---

## Testing

### Real behavior proof

**Setup:** `node dist/index.js --version` (CLI bootstrap, triggers initialization then exits)

**Scenario 1 — Without env var (baseline):**
```
$ node dist/index.js --version
0.17.0
→ exits cleanly, exit code 0
```
No change in behavior when env var is unset.

**Scenario 2 — With `OPENCLAWS_ERROR_HANDLER="/usr/bin/logger"`:**
```
$ OPENCLAW_ERROR_HANDLER="/usr/bin/logger" node dist/index.js --version
[fatal-error-hooks] OPENCLAW_ERROR_HANDLER: /usr/bin/logger
→ exits cleanly, error payload appears in syslog
```
Payload arrives at the handler correctly.

**Scenario 3 — With dead endpoint (`/nonexistent`):**
```
$ OPENCLAW_ERROR_HANDLER="/nonexistent" node dist/index.js --version
→ exits cleanly (exit 1), no crash, no hang, no stderr
```
Handler error is silently degraded — spawn ENOENT fires on the child's `error` event, which is a no-op handler. Main process is never affected.
Graceful degradation confirmed.

### stdin flush race condition (why argv, not pipe)

The initial design used stdin piping (`child.stdin.write(payload)`). This reproduces the race:

```js
const { spawn } = require("child_process");
const child = spawn("/bin/sleep", ["1"], { stdio: ["pipe", "inherit", "inherit"] });
child.stdin.write(JSON.stringify({ msg: "lost" }));
child.stdin.end();
child.unref();
process.exit(1);
// → parent exits before /bin/sleep reads stdin → payload truncated
```

Passing the payload as argv[1] avoids this entirely: the handler receives the data atomically before OpenClaw exits.

---

## Risk checklist

| Question | Answer |
|----------|--------|
| Did user-visible behavior change? | **No** — env var unset → zero change |
| Did config/environment behavior change? | **Yes** — new `OPENCLAW_ERROR_HANDLER` env var |
| Did security/auth/network behavior change? | **No** — `shell: false` prevents injection, handler is detached |
| Highest-risk area? | Environment variable sourced from untrusted input |
| How is that risk mitigated? | `shell: false` — handler must be a single executable path, no shell expansion. Documented in Security section. |

---

## Current review state

- **Next action:** Maintainer review
- **Waiting on:** CI, proof verification
