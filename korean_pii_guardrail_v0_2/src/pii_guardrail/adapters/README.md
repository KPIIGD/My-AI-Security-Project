# `pii_guardrail.adapters` — attach the guardrail to any gateway

One core engine, two attachment primitives, six concrete adapters. Every
adapter funnels through [`core.py`](core.py) so detection/masking behaviour and
the no-raw-PII boundary are identical everywhere.

```
                       ┌─────────────────────────────┐
                       │   pii_guardrail (core lib)   │
                       │   GuardrailPipeline / v3 NER │
                       └──────────────┬──────────────┘
                                      │
                       ┌──────────────▼──────────────┐
                       │ adapters.core  scan()/mask() │   ← single entry point
                       └───┬───────────────────────┬──┘
              in-process   │                       │   HTTP (sidecar contract)
        ┌──────────────────▼─────┐        ┌────────▼─────────────────────────┐
        │ KoreanPIIValidator     │        │ create_sidecar_app  /v1/pii/apply │
        │   (Guardrails AI)      │        │  ← LiteLLM hook / Azure APIM /    │
        │ scan()/mask_text()     │        │     Portkey / reverse proxy       │
        └────────────────────────┘        └───────────────────────────────────┘
```

## Two primitives

| primitive | how | who uses it |
|---|---|---|
| **in-process** | `import` and call `scan()` / `mask_text()` / `KoreanPIIValidator` | Guardrails AI, any code embed |
| **HTTP sidecar** | run `create_sidecar_app()` (one contract: `POST /v1/pii/apply`) | LiteLLM, Azure APIM, Portkey, reverse proxy |

Build the sidecar once → every network gateway reuses it.

## Install

```bash
pip install korean-pii-guardrail[adapters]      # fastapi + httpx (sidecar/proxy/portkey)
pip install korean-pii-guardrail[guardrails]    # Guardrails AI validator
pip install korean-pii-guardrail[litellm]       # LiteLLM hook
```

`import pii_guardrail.adapters` never requires any of these — each adapter
imports its dependency lazily.

## Config (env)

| var | meaning |
|---|---|
| `PII_CONFIG_DIR` | v0.2 configs dir (auto-located from the package if unset) |
| `NER_MODEL_PATH` | NER v3 model dir. Unset → regex + dictionary detectors only (`ner_mode="mock-ner"`) |
| `PII_ALLOW_MOCK` | `1` → fall back to mock if real NER load fails. Default fail-closed |
| `PII_FAIL_OPEN` | LiteLLM hook only: `1` → pass on guardrail error (default fail-closed) |
| `PII_SIDECAR_URL` | LiteLLM hook only: set → HTTP mode; unset → in-process |

## Adapters

### 1. Guardrails AI (in-process)
```python
from guardrails import Guard
from pii_guardrail.adapters import KoreanPIIValidator

guard = Guard().use(KoreanPIIValidator(on_fail="fix"))
print(guard.validate("내 번호 010-1234-5678").validated_output)   # → masked
```

### 2. HTTP sidecar (the shared contract)
```bash
uvicorn pii_guardrail.adapters.sidecar:app --host 0.0.0.0 --port 8080
curl -s localhost:8080/v1/pii/apply -H 'content-type: application/json' \
     -d '{"text":"내 번호 010-1234-5678"}'
```

### 3. LiteLLM hook
```yaml
# config.yaml
guardrails:
  - guardrail_name: "korean-pii"
    litellm_params:
      guardrail: pii_guardrail.adapters.litellm_hook.KoreanPIIGuardrail
      mode: "pre_call"
      default_on: true
```
In-process by default; set `PII_SIDECAR_URL` to isolate the heavy NER model.

### 4. Generic OpenAI-compatible reverse proxy (we become the gateway)
```bash
OPENAI_BASE_URL=https://api.openai.com/v1 \
  uvicorn pii_guardrail.adapters.reverse_proxy:app --port 8000
```
```python
OpenAI(base_url="http://localhost:8000/v1", api_key="sk-...")
```
Streaming not yet supported (`stream` is forced off so I/O can be scanned).

### 5. Portkey webhook
```bash
uvicorn pii_guardrail.adapters.portkey_webhook:app --port 8081
```
Register `https://.../guardrails/portkey` as a Webhook guardrail in Portkey.
The payload→response mapping is [`process_portkey_payload`](portkey_webhook.py);
confirm the field paths against your Portkey version.

### 6. Azure APIM
APIM has no native hook — use [`azure_apim_policy.xml`](azure_apim_policy.xml),
which calls the sidecar via `<send-request>` and rewrites the request body
(fail-closed on sidecar error).

## Not attachable (be honest)

| gateway | why |
|---|---|
| AWS Bedrock Guardrails | black box — run our normalization *beside* it, not inside |
| Helicone | observability only, no enforcement hook |
| Cloudflare AI Gateway | no native hook — would need a Worker |
| Kong (OSS) | clean only on Enterprise; OSS needs a custom Lua/Go plugin |
