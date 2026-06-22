# Kong — attach the Korean PII guardrail

Kong has no native "guardrail" hook, but the bundled **serverless-functions**
plugin (`pre-function` / `post-function`, Lua) can call our sidecar over HTTP —
the same `/v1/pii/apply` contract LiteLLM uses. Run the sidecar first:

```bash
uvicorn pii_guardrail.adapters.sidecar:app --port 8080   # PII_SIDECAR_URL target
```

> Verification: this config is provided as a tested-by-inspection artifact —
> we don't have a live Kong here. The sidecar call/contract is the same one
> verified for LiteLLM. Confirm Lua module availability on your Kong build
> (`lua-resty-http` ships with Kong Gateway).

## DB-less declarative config (`kong.yml`)

```yaml
_format_version: "3.0"
services:
  - name: openai
    url: https://api.openai.com
    routes:
      - name: chat
        paths: ["/v1/chat/completions"]
    plugins:
      - name: pre-function          # INPUT guard: mask / block before upstream
        config:
          access:
            - |
              local http  = require("resty.http")
              local cjson = require("cjson.safe")
              local SIDE  = os.getenv("PII_SIDECAR_URL")    -- e.g. http://pii-sidecar:8080/v1/pii/apply
              local raw   = kong.request.get_raw_body()
              local data  = raw and cjson.decode(raw)
              if data and data.messages then
                for _, m in ipairs(data.messages) do
                  if type(m.content) == "string" then
                    local res = http.new():request_uri(SIDE, {
                      method  = "POST",
                      headers = { ["Content-Type"] = "application/json" },
                      body    = cjson.encode({ text = m.content,
                                               policy_profile = "strict",
                                               scan_stage = "input" }),
                    })
                    -- fail-closed: any non-200 blocks rather than leaking PII
                    if not res or res.status ~= 200 then
                      return kong.response.exit(503, { error = "PII guardrail unavailable" })
                    end
                    local out = cjson.decode(res.body)
                    if out.blocked then
                      return kong.response.exit(400, { error = "blocked by Korean PII guardrail" })
                    end
                    m.content = out.masked_text or m.content
                  end
                end
                kong.service.request.set_raw_body(cjson.encode(data))
              end
```

> ⚠️ **This config guards INPUT only.** The model's RESPONSE is unguarded until
> you add the output filter below — a model can still emit PII. Add a
> `post-function` that reads `kong.service.response` body, calls the sidecar with
> `scan_stage="output"`, and rewrites `choices[].message.content` (redact, never
> return raw, on a non-200 — fail-closed). For full coverage, prefer routing
> through our reverse proxy ([reverse_proxy.py](reverse_proxy.py)) which guards
> both directions.

## Alternative: custom plugin

For production, package the same logic as a custom Lua/Go plugin
(`handler.lua` `access`/`body_filter` phases) instead of inline serverless code.
The HTTP call to the sidecar is identical.
