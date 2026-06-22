# Apache APISIX — attach the Korean PII guardrail

APISIX's `serverless-pre-function` / `serverless-post-function` plugins (Lua)
call our sidecar over HTTP — the same `/v1/pii/apply` contract LiteLLM uses.
Run the sidecar first:

```bash
uvicorn pii_guardrail.adapters.sidecar:app --port 8080
```

> Verification: tested-by-inspection artifact (no live APISIX here). The sidecar
> contract is the one verified for LiteLLM. `resty.http` ships with APISIX.

## Route config (Admin API JSON)

```jsonc
{
  "uri": "/v1/chat/completions",
  "upstream": { "type": "roundrobin", "nodes": { "api.openai.com:443": 1 }, "scheme": "https" },
  "plugins": {
    "serverless-pre-function": {
      "phase": "rewrite",
      "functions": ["return function(conf, ctx)\n  local http  = require('resty.http')\n  local cjson = require('cjson.safe')\n  local core  = require('apisix.core')\n  local SIDE  = os.getenv('PII_SIDECAR_URL')\n  local body  = core.request.get_body()\n  local data  = body and cjson.decode(body)\n  if data and data.messages then\n    for _, m in ipairs(data.messages) do\n      if type(m.content) == 'string' then\n        local res = http.new():request_uri(SIDE, { method='POST',\n          headers={['Content-Type']='application/json'},\n          body=cjson.encode({text=m.content, policy_profile='strict', scan_stage='input'}) })\n        if not res or res.status ~= 200 then\n          return core.response.exit(503, { error = 'PII guardrail unavailable' })\n        end\n        local out = cjson.decode(res.body)\n        if out.blocked then\n          return core.response.exit(400, { error = 'blocked by Korean PII guardrail' })\n        end\n        m.content = out.masked_text or m.content\n      end\n    end\n    core.request.set_body(ctx, cjson.encode(data))\n  end\nend"]
    }
  }
}
```

Notes:
- Fail-closed: any non-200 from the sidecar returns 503 instead of forwarding.
- ⚠️ **This config guards INPUT only — the model RESPONSE is unguarded** until you
  add the output filter. Add `serverless-post-function` (phase `body_filter`) that
  calls the sidecar with `scan_stage="output"` and rewrites
  `choices[].message.content` (redact on error — never raw). For full coverage,
  prefer routing through our reverse proxy ([reverse_proxy.py](reverse_proxy.py)),
  which guards both directions.
- For heavier logic, write a custom APISIX plugin or use `ext-plugin-pre-req`
  (external plugin runner) instead of inline Lua. The sidecar call is identical.
