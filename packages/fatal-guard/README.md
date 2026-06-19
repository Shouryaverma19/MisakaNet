# @misakanet/fatal-guard

> Zero-dependency non-invasive fatal error guard for Node.js CLIs.  
> Capture uncaught exceptions, unhandled rejections, and non-zero exits — route structured 4-field payload to an external handler.

## Why

Vite, E2B, OpenClaw — three major CLI tools all lack a standard mechanism to hook external alerting into the fatal-error lifecycle.  
This package provides that entry point without modifying any source code.

```
node -r @misakanet/fatal-guard/register ./node_modules/.bin/vite build
```

No fork. No PR. No dependency. One env var.

## Usage

### Automatic registration (recommended)

```bash
FATAL_HANDLER=/usr/bin/logger node -r @misakanet/fatal-guard/register ./app.js
```

### Manual registration

```js
const { runHandler } = require('@misakanet/fatal-guard');

process.on('uncaughtException', (err) => {
  runHandler('uncaught_exception');
});
```

## Payload (4 fields)

When a fatal event occurs, the handler is spawned with a single JSON argv argument:

```json
{
  "schemaVersion": 1,
  "reason": "uncaught_exception",
  "timestamp": "2026-06-19T04:20:00.000Z",
  "pid": 12345
}
```

| Field | Type | Description |
|-------|------|-------------|
| `schemaVersion` | number | Payload format version (always 1) |
| `reason` | string | `uncaught_exception` · `unhandled_rejection` · `exit_code` |
| `timestamp` | string | ISO 8601 |
| `pid` | number | Process ID (for log correlation) |

## Handler

The handler is any executable on `$PATH` (or absolute path). Common examples:

```bash
# syslog
FATAL_HANDLER=/usr/bin/logger

# custom script
FATAL_HANDLER=/opt/alert-to-slack.sh

# HTTP POST via curl
FATAL_HANDLER=/usr/bin/curl
# (will receive JSON as argv[1] — pipe-aware handlers expected)
```

## Design

| Principle | Implementation |
|-----------|---------------|
| Zero dependencies | `require('node:child_process')` only |
| Non-blocking | `spawn` + `detached: true` + `unref()` — never blocks shutdown |
| Injection-safe | `shell: false` — no shell interpretation of env var or payload |
| Fire-and-forget | Handler failure is silently swallowed |

## Related

- [OpenClaw PR #93310](https://github.com/openclaw/openclaw/pull/93310) — origin of the 4-field model
- [E2B PR #1458](https://github.com/e2b-dev/E2B/pull/1458) — parallel implementation
- [Vite PR #22701](https://github.com/vitejs/vite/pull/22701) — parallel implementation
