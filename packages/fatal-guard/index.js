#!/usr/bin/env node
/**
 * @misakanet/fatal-guard
 *
 * Zero-dependency non-invasive fatal error guard.
 *
 * This module exports:
 *   - buildPayload(reason)  — Build a 4-field JSON payload
 *   - runHandler(reason)    — Fire the external handler (if FATAL_HANDLER is set)
 *   - FatalPayload          — Type signature (JSDoc)
 *
 * For automatic hook registration, use:
 *   node -r @misakanet/fatal-guard/register ./app.js
 *
 * Or import and attach manually:
 *   const { runHandler } = require('@misakanet/fatal-guard');
 *   process.on('uncaughtException', (err) => runHandler('uncaught_exception'));
 */

const { spawn } = require('node:child_process');

/**
 * @typedef {Object} FatalPayload
 * @property {number} schemaVersion — Payload format version (always 1)
 * @property {string} reason — "uncaught_exception" | "unhandled_rejection" | "exit_code"
 * @property {string} timestamp — ISO 8601 timestamp
 * @property {number} pid — Process ID
 */

/** Build a 4-field JSON payload string. @param {string} reason @returns {string} */
function buildPayload(reason) {
  return JSON.stringify({
    schemaVersion: 1,
    reason,
    timestamp: new Date().toISOString(),
    pid: process.pid,
  });
}

/**
 * Fire-and-forget external handler invocation.
 * Reads FATAL_HANDLER env var, spawns with 4-field JSON payload as argv[1].
 * Never throws. Never blocks shutdown.
 *
 * @param {string} reason
 */
function runHandler(reason) {
  const handler = (process.env.FATAL_HANDLER || '').trim();
  if (!handler) return;

  try {
    const payload = buildPayload(reason);
    const child = spawn(handler, [payload], {
      stdio: 'ignore',
      detached: true,
      shell: false,
    });
    child.on('error', () => {});
    child.unref();
  } catch (_) {}
}

module.exports = { buildPayload, runHandler };
