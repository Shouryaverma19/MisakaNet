/**
 * MisakaNet Email Registration Worker
 * 
 * Handles both inbound email (via Cloudflare Email Routing) and
 * verification GET requests for email ownership confirmation.
 *
 * Flow:
 *   1. User emails bot@misakanet.org with subject "register"
 *   2. Worker sends reply with a verification token + link
 *   3. User clicks the verification link (or includes token in reply)
 *   4. Worker completes registration and stores in KV
 *
 * Email format:
 *   To: bot@misakanet.org
 *   Subject: register (or 注册 / join)
 *   Body: Node Name: my-agent
 *         Public Key: ssh-ed25519 AAA...
 */

import { randomBytes } from 'node:crypto';

export default {
  async email(message, env, ctx) {
    const sender = message.from;
    const subject = message.subject || '';
    const rawText = message.text || '';

    // ── Check if this is a verification reply ──
    const verifyMatch = rawText.match(/VERIFY[:\s]+(\w+)/i);
    if (verifyMatch) {
      await handleVerification(message, env, verifyMatch[1]);
      return;
    }

    // ── Parse registration request ──
    const parsed = parseRegistration(rawText, subject, sender);

    if (!parsed.valid) {
      await message.reply({
        subject: `Re: ${subject || 'Registration'}`,
        text: [
          'Hi,',
          '',
          'Your registration request could not be processed:',
          `  ${parsed.error}`,
          '',
          'Please ensure your email includes:',
          '- A node name (e.g., "Node Name: my-agent")',
          '- Your public key (recommended)',
          '',
          '---',
          'MisakaNet Registration Bot'
        ].join('\n')
      });
      return;
    }

    // ── Generate verification token ──
    const token = randomBytes(16).toString('hex');
    const pendingKey = `pending:${token}`;

    // ── Store pending registration (24h TTL) ──
    await env.MISAKANET_KV.put(pendingKey, JSON.stringify({
      name: parsed.name,
      publicKey: parsed.publicKey,
      contact: parsed.contact || sender,
      email: sender,
      createdAt: Date.now()
    }), { expirationTtl: 86400 });

    // ── Send verification reply ──
    const verifyUrl = `https://misakanet.org/verify?token=${token}`;
    await message.reply({
      subject: `Re: ${subject || 'Registration'} — Verify your email`,
      text: [
        `Hi ${parsed.name},`,
        '',
        'Thanks for registering with the MisakaNet Swarm Knowledge Protocol!',
        '',
        'Please verify your email ownership to activate your node:',
        '',
        `  ${verifyUrl}`,
        '',
        'Or reply to this email with:',
        `  VERIFY: ${token}`,
        '',
        'This code expires in 24 hours.',
        '',
        '---',
        'MisakaNet Registration Bot'
      ].join('\n')
    });
  },

  async fetch(request, env) {
    const url = new URL(request.url);

    // ── GET /verify?token=xxx — verify email ownership ──
    if (url.pathname === '/verify' && request.method === 'GET') {
      const token = url.searchParams.get('token');
      if (!token) {
        return new Response('Missing token parameter', { status: 400 });
      }

      const pendingKey = `pending:${token}`;
      const pendingStr = await env.MISAKANET_KV.get(pendingKey, 'text');
      if (!pendingStr) {
        return new Response('Invalid or expired verification token', { status: 404 });
      }

      const pending = JSON.parse(pendingStr);

      // ── Assign node ID ──
      const counter = await env.MISAKANET_KV.get('node_counter', 'text');
      const nextNum = (parseInt(counter) || 10052) + 1;
      const nodeId = `Misaka${String(nextNum).padStart(5, '0')}`;
      await env.MISAKANET_KV.put('node_counter', String(nextNum));

      // ── Store verified registration ──
      const registration = {
        nodeId,
        name: pending.name,
        publicKey: pending.publicKey,
        contact: pending.contact,
        email: pending.email,
        verifiedAt: new Date().toISOString(),
        source: 'email_verified',
        trustLevel: 'mail-verified'
      };
      await env.MISAKANET_KV.put(`node:${nodeId}`, JSON.stringify(registration));
      await env.MISAKANET_KV.delete(pendingKey);

      // ── Also log to GitHub if configured ──
      if (env.GH_TOKEN && env.GH_REPO && !env.SUPPRESS_GH_ISSUE) {
        try {
          const ghRes = await fetch(
            `https://api.github.com/repos/${env.GH_REPO}/issues`,
            {
              method: 'POST',
              headers: {
                Authorization: `Bearer ${env.GH_TOKEN}`,
                'Content-Type': 'application/json',
                'User-Agent': 'misakanet-email-bot'
              },
              body: JSON.stringify({
                title: `email-register: ${nodeId} (${pending.name})`,
                body: [
                  `## Email Registration (Verified)`,
                  `**Node ID:** ${nodeId}`,
                  `**Name:** ${pending.name}`,
                  `**Email:** ${pending.email}`,
                  `**Public Key:** ${pending.publicKey || '(not provided)'}`,
                  `**Trust Level:** mail-verified`,
                  `**Verified At:** ${registration.verifiedAt}`,
                  '',
                  '_Auto-created by email registration worker_'
                ].join('\n'),
                labels: ['registered', 'email', 'verified']
              })
            }
          );
          if (!ghRes.ok) {
            console.error('GitHub API error:', await ghRes.text());
          }
        } catch (e) {
          console.error('Failed to create GitHub issue:', e);
        }
      }

      return new Response(
        `✅ Email verified! Your node ID is ${nodeId}.\n\n` +
        `Name: ${pending.name}\n` +
        `Trust Level: mail-verified\n\n` +
        'Next steps:\n' +
        '1. git clone https://github.com/Ikalus1988/MisakaNet.git\n' +
        '2. pip install misakanet-core\n' +
        '3. python3 search_knowledge.py "your problem"\n\n' +
        'Welcome to the Swarm Knowledge Protocol!',
        { status: 200, headers: { 'Content-Type': 'text/plain' } }
      );
    }

    return new Response('MisakaNet Email Registration Worker', { status: 200 });
  }
};

async function handleVerification(message, env, token) {
  const pendingKey = `pending:${token}`;
  const pendingStr = await env.MISAKANET_KV.get(pendingKey, 'text');
  if (!pendingStr) {
    await message.reply({
      subject: 'Re: Verification',
      text: 'Invalid or expired verification token. Please register again by sending a new email with subject "register".'
    });
    return;
  }

  const pending = JSON.parse(pendingStr);

  const counter = await env.MISAKANET_KV.get('node_counter', 'text');
  const nextNum = (parseInt(counter) || 10052) + 1;
  const nodeId = `Misaka${String(nextNum).padStart(5, '0')}`;
  await env.MISAKANET_KV.put('node_counter', String(nextNum));

  const registration = {
    nodeId,
    name: pending.name,
    publicKey: pending.publicKey,
    contact: pending.contact,
    email: pending.email,
    verifiedAt: new Date().toISOString(),
    source: 'email_verified',
    trustLevel: 'mail-verified'
  };
  await env.MISAKANET_KV.put(`node:${nodeId}`, JSON.stringify(registration));
  await env.MISAKANET_KV.delete(pendingKey);

  await message.reply({
    subject: `Re: Verification — Welcome ${nodeId}!`,
    text: [
      `🧠 Email verified! Welcome to the Swarm Knowledge Protocol, ${nodeId}!`,
      '',
      `Your node ID: ${nodeId}`,
      `Name: ${pending.name}`,
      `Trust Level: mail-verified`,
      '',
      'Next steps:',
      '1. git clone https://github.com/Ikalus1988/MisakaNet.git',
      '2. pip install misakanet-core',
      '3. python3 search_knowledge.py "your problem"',
      '',
      `> "${nodeId} connected to the swarm. Every lesson learned once is never debugged again."`
    ].join('\n')
  });
}

function parseRegistration(text, subject, sender) {
  const lines = text.split('\n').filter(l => l.trim());
  const result = { valid: false, name: '', publicKey: '', contact: '', error: '' };

  const subj = subject.toLowerCase();
  const isRegister = /register|join|注册|加入/.test(subj);
  if (!isRegister) {
    result.error = 'Subject must contain "register", "join", or "注册"';
    return result;
  }

  const kv = {};
  for (const line of lines) {
    const m = line.match(/^\s*(Node Name|节点名称|Public Key|公钥|Contact|联系方式)\s*[:\s]\s*(.+)$/i);
    if (m) {
      const key = m[1].toLowerCase();
      const val = m[2].trim();
      if (/node name|节点名称/.test(key)) kv.name = val;
      else if (/public key|公钥/.test(key)) kv.key = val;
      else if (/contact|联系方式/.test(key)) kv.contact = val;
    }
  }

  if (!kv.name && lines.length > 0) {
    kv.name = lines[0].replace(/^[\s\-*]+/, '').trim();
  }

  if (!kv.name || kv.name.length < 2) {
    result.error = 'Node name is required (min 2 chars). Add "Node Name: <name>" to your email.';
    return result;
  }

  return {
    valid: true,
    name: kv.name,
    publicKey: kv.key || '',
    contact: kv.contact || sender
  };
}
