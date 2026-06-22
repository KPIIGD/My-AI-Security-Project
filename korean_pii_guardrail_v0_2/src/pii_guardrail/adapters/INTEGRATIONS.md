# Integration catalog — where the Korean PII guardrail attaches

One core engine ([`core.py`](core.py)), two attachment primitives, many gateways.
Build the **sidecar once** and every network gateway reuses the same
`POST /v1/pii/apply` contract; embed **in-process** for frameworks and SDKs.

Legend — **Verified**: ✅ run-verified locally · 🧪 logic/contract verified
(dep or platform absent) · 📄 config artifact (inspection only).

## LLM gateways with a custom hook (like LiteLLM)

| Gateway | How we attach | Primitive | File | Verified |
|---|---|---|---|---|
| **LiteLLM** | `CustomGuardrail` hook (in-process or HTTP sidecar) | both | [litellm_hook.py](litellm_hook.py) | ✅ |
| **Portkey** | custom Webhook guardrail | HTTP | [portkey_webhook.py](portkey_webhook.py) | ✅ (synthetic payload) |
| **Azure APIM** | `<send-request>` inbound policy → sidecar | HTTP | [azure_apim_policy.xml](azure_apim_policy.xml) | 📄 |
| **Kong** | `pre/post-function` (Lua) → sidecar, or custom plugin | HTTP | [kong.md](kong.md) | 📄 |
| **Apache APISIX** | `serverless-pre/post-function` → sidecar | HTTP | [apisix.md](apisix.md) | 📄 |
| **Cloudflare AI Gateway** | Worker at the edge → sidecar | HTTP | [cloudflare_worker.js](cloudflare_worker.js) | 📄 |
| **Envoy** | reverse-proxy cluster (mask) / `ext_authz` (block-only) | HTTP | [envoy.md](envoy.md) | 📄 (Option A reuses ✅ proxy) |

## We become the gateway

| Form | How | Primitive | File | Verified |
|---|---|---|---|---|
| **OpenAI-compatible reverse proxy** | point `base_url` at us; we mask in/out + forward | HTTP | [reverse_proxy.py](reverse_proxy.py) | ✅ (block/mask logic) |
| **ASGI middleware** | drop into your own FastAPI/Starlette app | in-process | [asgi_middleware.py](asgi_middleware.py) | ✅ |
| **HTTP sidecar** | the shared `/v1/pii/apply` contract everything above calls | HTTP | [sidecar.py](sidecar.py) | ✅ (live uvicorn) |

## Guardrail / agent frameworks (in-process embed)

| Framework | How we attach | File | Verified |
|---|---|---|---|
| **Guardrails AI** | custom `Validator` | [guardrails_ai.py](guardrails_ai.py) | 🧪 (guardrails not installed) |
| **NeMo Guardrails** | custom `korean_pii_mask` action | [nemo_guardrails.py](nemo_guardrails.py) | ✅ action / 🧪 registration |
| **LangChain** | `mask_input()` / `mask_output()` runnables, `protect(llm)` | [langchain.py](langchain.py) | ✅ |

## SDK / provider client wrappers (in-process)

| Target | How we attach | File | Verified |
|---|---|---|---|
| **OpenAI / Azure OpenAI / any OpenAI-compatible SDK** | `guard_openai(client)` wraps `chat.completions.create` | [openai_wrapper.py](openai_wrapper.py) | ✅ |
| **AWS Bedrock** | `guard_bedrock(client)` wraps the Converse API (client-side complement) | [bedrock.py](bedrock.py) | ✅ |

## Not attachable (honest)

| Gateway | Why |
|---|---|
| **AWS Bedrock Guardrails (inside)** | black box — can't run our Korean detector *inside* it. We complement on the client (`bedrock.py`), running first. |
| **Helicone** | observability/caching only — no enforcement hook to mask/block. Use it *alongside* (it logs our masked traffic). |

## Quick start (any of the above)

```bash
pip install -e ".[adapters]"      # fastapi+httpx+uvicorn (sidecar/proxy/middleware)
# plus, as needed:  .[langchain]  .[guardrails]  .[litellm]   (openai/boto3 you likely already have)

# the one server every network gateway calls:
uvicorn pii_guardrail.adapters.sidecar:app --port 8080
```

All gateway deps are lazy-imported: `import pii_guardrail.adapters` pulls in
**none** of fastapi/httpx/openai/boto3/langchain/litellm/guardrails. Every
adapter is **fail-closed** (errors block/redact, never leak raw PII) and emits
only no-raw-PII summaries.
