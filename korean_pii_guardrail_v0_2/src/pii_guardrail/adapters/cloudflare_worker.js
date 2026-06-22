/**
 * Cloudflare AI Gateway — Korean PII guardrail at the edge.
 *
 * Cloudflare AI Gateway has no native guardrail hook, so we put a Worker in
 * front of it (or in front of the provider). The Worker masks PII in the
 * request, then forwards to the upstream; it calls our sidecar over HTTP — the
 * same /v1/pii/apply contract LiteLLM uses.
 *
 * Bindings / vars (wrangler.toml):
 *   PII_SIDECAR_URL   e.g. https://pii-sidecar.example.com/v1/pii/apply
 *   OPENAI_BASE_URL   upstream, e.g. https://gateway.ai.cloudflare.com/v1/<acct>/<gw>/openai
 *                     (or https://api.openai.com)
 *
 * Verification: tested-by-inspection artifact (no live Cloudflare here). The
 * sidecar contract is the one verified for LiteLLM.
 *
 * Note: streaming (stream:true) is forced off so input/output can be scanned.
 */

const BLOCKED_MSG = "[응답이 개인정보 보호 정책에 의해 차단되었습니다.]";

async function scanText(env, text, stage) {
  const r = await fetch(env.PII_SIDECAR_URL, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text, policy_profile: "strict", scan_stage: stage }),
  });
  if (!r.ok) throw new Error("pii-sidecar " + r.status); // fail-closed
  return r.json();
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== "POST" || !url.pathname.endsWith("/v1/chat/completions")) {
      return fetch(env.OPENAI_BASE_URL + url.pathname, request); // passthrough
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response(JSON.stringify({ error: "invalid JSON" }), { status: 400 });
    }
    body.stream = false;

    // INPUT: mask / block (fail-closed)
    try {
      if (Array.isArray(body.messages)) {
        for (const m of body.messages) {
          if (typeof m.content === "string") {
            const out = await scanText(env, m.content, "input");
            if (out.blocked) {
              return new Response(
                JSON.stringify({ error: { type: "pii_blocked", message: "blocked by Korean PII guardrail" } }),
                { status: 400, headers: { "content-type": "application/json" } }
              );
            }
            m.content = out.masked_text ?? m.content;
          }
        }
      }
    } catch (e) {
      return new Response(JSON.stringify({ error: "PII guardrail unavailable (fail-closed)" }), { status: 503 });
    }

    // forward to upstream
    const upstream = await fetch(env.OPENAI_BASE_URL + "/v1/chat/completions", {
      method: "POST",
      headers: { "content-type": "application/json", authorization: request.headers.get("authorization") || "" },
      body: JSON.stringify(body),
    });

    let data;
    try {
      data = await upstream.json();
    } catch {
      return new Response(await upstream.text(), { status: upstream.status });
    }

    // OUTPUT: mask (fail-closed → redact, never raw)
    for (const choice of data.choices || []) {
      const c = choice.message?.content;
      if (typeof c === "string" && c.trim()) {
        try {
          const out = await scanText(env, c, "output");
          choice.message.content = out.blocked ? BLOCKED_MSG : (out.masked_text ?? c);
        } catch {
          choice.message.content = BLOCKED_MSG;
        }
      }
    }

    return new Response(JSON.stringify(data), {
      status: upstream.status,
      headers: { "content-type": "application/json" },
    });
  },
};
