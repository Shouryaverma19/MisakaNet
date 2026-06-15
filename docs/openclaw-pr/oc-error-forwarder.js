#!/usr/bin/env node
/**
 * OpenClaw Error Forwarder — 参考实现
 *
 * 配合 OPENCLAW_ERROR_HANDLER 使用。接收 OpenClaw 崩溃时的 JSON payload,
 * 解析后转发到飞书 Webhook / 日志文件 / 其他渠道。
 *
 * 用法:
 *   export OPENCLAW_ERROR_HANDLER="/path/to/oc-error-forwarder.js"
 *
 * 支持的环境变量:
 *   OC_FORWARDER_WEBHOOK — 飞书 Webhook URL (可选)
 *   OC_FORWARDER_LOG_DIR — 日志目录 (可选, 默认 /var/log/openclaw/)
 *
 * 设计原则:
 * - 零 npm 依赖 (纯 Node.js stdlib)
 * - 失败不抛异常 (write 失败静默降级)
 * - 同步写日志 (确保进程退出前落盘)
 */

const fs = require("fs");
const path = require("path");
const os = require("os");

// ── 解析 argv ──
// OpenClaw 把 JSON payload 作为第一个参数传入
const payloadArg = process.argv[2];
if (!payloadArg) {
  process.exit(0);
}

let payload;
try {
  payload = JSON.parse(payloadArg);
} catch {
  // payload 非 JSON, 不重要
  process.exit(0);
}

// ── 格式化输出 ──
const hostname = os.hostname();
const reason = payload.reason || "unknown";
const name = payload.name || "";
const message = payload.message || "";
const stack = payload.stack || "";
const timestamp = payload.timestamp || new Date().toISOString();

const summary = [
  `[OpenClaw Error] ${hostname} — ${reason}`,
  name && message ? `  ${name}: ${message}` : "",
  stack ? `  Stack:\n${stack.split("\n").map(l => `    ${l}`).join("\n")}` : "",
  `  At: ${timestamp}`,
].filter(Boolean).join("\n");

// ── 1. 写日志文件 (同步, 确保落盘) ──
const logDir = process.env.OC_FORWARDER_LOG_DIR || "/var/log/openclaw";
try {
  fs.mkdirSync(logDir, { recursive: true });
  const logPath = path.join(logDir, "errors.log");
  fs.appendFileSync(logPath, summary + "\n---\n");
} catch {
  // 写日志失败不阻塞
}

// ── 2. 飞书 Webhook (异步, fire-and-forget) ──
const webhook = process.env.OC_FORWARDER_WEBHOOK;
if (webhook) {
  const body = JSON.stringify({
    msg_type: "interactive",
    card: {
      header: {
        title: { tag: "plain_text", content: `🚨 OpenClaw Error: ${reason}` },
        template: "red",
      },
      elements: [
        { tag: "markdown", content: `**Host:** ${hostname}\n**Error:** ${name}: ${message}` },
        { tag: "markdown", content: `\`\`\`\n${stack.slice(0, 1000)}\n\`\`\`` },
        { tag: "note", elements: [{ tag: "plain_text", content: `schemaVersion: ${payload.schemaVersion || "N/A"} · ${timestamp}` }] },
      ],
    },
  });

  const http = webhook.startsWith("https") ? require("https") : require("http");
  const url = new URL(webhook);
  const req = http.request(
    { hostname: url.hostname, path: url.pathname, method: "POST", headers: { "Content-Type": "application/json" } },
    () => {},
  );
  req.on("error", () => {});
  req.write(body);
  req.end();
}
