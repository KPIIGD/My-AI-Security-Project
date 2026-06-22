# Attaching the Korean PII Guardrail to LLM Gateways — Research Report & Integration Guide

**Project:** Korean PII Guardrail (`korean_pii_guardrail_v0_2`) — capstone deployment docs
**Date:** 2026-06-23
**Scope:** How to attach our Korean PII detection/masking guardrail to major LLM gateways, proxies, and guardrail frameworks.
**Sources:** current (2025–2026) vendor docs; URLs cited per section. Items we could not confirm against a live doc are marked **[UNVERIFIED]**.

---

## 0. What we are attaching (the integration surface)

Our guardrail already exposes two stable interfaces. Every gateway pattern below targets one of them.

**(a) FastAPI sidecar** — `pii-sidecar/app.py`. Heavy NER (torch, ~1.3 GB model) is isolated here; the gateway only makes an HTTP call.

```
POST /v1/pii/apply
  body:  { "text": str, "policy_profile": "strict", "scan_stage": "input"|"output", "request_id"?: str }
  reply: { "blocked": bool,
           "masked_text": str | null,
           "spans": [ { start, end, entity_type, score, risk_level, action, value_hash, ... } ],
           "metrics": { latency_ms, detected_span_count, masked_span_count },
           "ner_mode": str }
GET  /health  → { status, ner_mode, config_dir }
```

Design contract worth preserving across every integration (from `schema.py` / `app.py`):
- **No-raw-PII boundary.** Spans carry an HMAC `value_hash`, never the raw value (`raw_value_logged: false`). Only `masked_text` ever leaves the service. Keep this true at every gateway boundary — do not log the gateway's own raw request/response traces unredacted.
- **Fail-closed by default.** The reference LiteLLM hook (`korean_pii_gateway_guardrail.py`) blocks if the sidecar call fails unless `PII_FAIL_OPEN=1`. Replicate this on every gateway (most gateways default to fail-*open*).
- **Two scan stages.** `scan_stage:"input"` (mask/block the prompt before the LLM) and `scan_stage:"output"` (mask the completion). Map each gateway's pre/post hook to these.

**(b) Pure-Python library** — `from pii_guardrail.pipeline import GuardrailPipeline; pipe.process(GuardrailRequest(text=...))`. Use this for in-process frameworks (NeMo Guardrails, Guardrails AI) to avoid a network hop.

**Rule of thumb:** **gateways/proxies** (LiteLLM, Portkey, Kong, Azure APIM, Cloudflare) call the **sidecar over HTTP**; **Python guardrail frameworks** (NeMo, Guardrails AI) embed the **library** directly.

---

## 1. LiteLLM (reference implementation — already built)

1. **What it is.** OpenAI-compatible proxy/SDK routing to 100+ providers, with a first-class guardrails system.
2. **Attach mechanism.** Subclass `litellm.integrations.custom_guardrail.CustomGuardrail` and register it in `config.yaml` under `guardrails:` with a `mode`. Lifecycle hooks:
   - `async_pre_call_hook(user_api_key_dict, cache, data, call_type)` — `mode: "pre_call"`, mutate/reject the **input** before the LLM call.
   - `async_post_call_success_hook(data, user_api_key_dict, response)` — mask the **output**.
   - `apply_guardrail(inputs, request_data, input_type, logging_obj)` — separate path used by the `/guardrails/apply_guardrail` API and the UI **Test Playground** (`mode: "during_call"` calls it by default). `inputs` is a `TypedDict` with `texts: List[str]`; access via dict API, never attributes. (This is the path that earlier appeared "not called" — `async_pre_call_hook` only fires on real LLM calls; the Playground/API path needs `apply_guardrail`.)
3. **Our integration.** Implemented in `korean_pii_gateway_guardrail.py`: a thin `CustomGuardrail` that `httpx.post`s the sidecar `/v1/pii/apply` from all three hooks. Register:
   ```yaml
   guardrails:
     - guardrail_name: "korean-pii"
       litellm_params:
         guardrail: korean_pii_gateway_guardrail.KoreanPIIGuardrail
         mode: "pre_call"          # add a second entry with mode "post_call" for output masking
         default_on: true
   ```
4. **Effort: Easy (done).** Gotchas: hooks must be `async def` (a sync `apply_guardrail` raises `object dict can't be used in 'await'`); the exact `apply_guardrail` signature is `(self, inputs, request_data, input_type, logging_obj=None)`; an import error in the registered module kills the container on boot (comment out, confirm `/health/liveness`, re-add).
5. **Docs:** https://docs.litellm.ai/docs/proxy/guardrails/custom_guardrail · https://docs.litellm.ai/docs/proxy/guardrails/quick_start

---

## 2. Portkey AI Gateway

1. **What it is.** AI gateway + observability (SaaS **and** open-source self-hostable `Portkey-AI/gateway`) routing to 1,600+ models via one OpenAI-compatible API, with a built-in Guardrails system.
2. **Attach mechanism.** First-class **"Bring Your Own Guardrails" → Webhook**. You configure a webhook URL + headers + timeout (default 3000 ms). It fires at both lifecycle points, distinguished by `eventType`: `beforeRequestHook` (input) and `afterRequestHook` (output).
   - Portkey **POSTs**: `{ request:{json,text,isStreamingRequest}, response:{json,text,statusCode}, provider, requestType, metadata, eventType }`.
   - Your webhook **returns**: `{ "verdict": bool, "transformedData": { request:{...}, response:{...} } }`. `verdict:false` triggers the configured action; `transformedData` lets you **override the body with masked content**.
   - Actions: sync + `DENY:true` → block (HTTP 446); sync + `DENY:false` → flag & continue (HTTP 246, use with `transformedData` for mask-and-continue); async → log-only.
3. **Our integration.** Webhook → our sidecar, via a **small adapter endpoint** (schemas differ). Add e.g. `POST /portkey/webhook` that maps `eventType`→`scan_stage`, extracts text from `request.json.messages` (input) or `response`, calls `/v1/pii/apply`, and returns `{verdict: not blocked, transformedData: <body with masked_text substituted>}`.
4. **Effort: Easy–Medium.** Gotchas:
   - **Fail-OPEN by default** — on timeout Portkey returns `verdict:true` (passes). This violates our fail-closed contract; there is no native fail-closed-on-timeout toggle, so keep latency well under the timeout and prefer sync+DENY.
   - **SaaS requires a publicly reachable webhook.** For a PII service, **self-host the open-source Portkey gateway** next to the sidecar so raw Korean PII stays in-network (enterprise private-network webhook access exists but the exact config is **[UNVERIFIED]**).
   - Only real work is the schema adapter (eventType↔scan_stage, mask re-injection into the OpenAI body).
5. **Docs:** https://portkey.ai/docs/product/guardrails · https://portkey.ai/docs/integrations/guardrails/bring-your-own-guardrails · https://github.com/Portkey-AI/gateway

---

## 3. Cloudflare AI Gateway

1. **What it is.** Hosted edge proxy between app and LLM providers adding caching, rate limiting, retries, fallback, analytics, DLP, and a built-in Guardrails feature.
2. **Attach mechanism.** **No native custom-guardrail hook.** Built-in Guardrails run **Llama Guard 3 (8B) on Workers AI** over fixed safety categories (input + output; Flag/Block/Ignore). Two blockers for us: **Korean is not in Llama Guard's supported languages**, and it does content-safety classification only (no PII, no `masked_text`). The escape hatch is **Cloudflare Workers**: arbitrary code in the request path that can `fetch()` external endpoints.
3. **Our integration.** **Worker-as-middleware:** Worker receives the request → `fetch()` our sidecar `/v1/pii/apply` (`scan_stage:"input"`) → if `blocked`, short-circuit; else forward `masked_text` to the LLM **through AI Gateway** (via the `env.AI`/gateway binding) → optionally re-scan the response (`scan_stage:"output"`) → return. You keep AI Gateway's caching/analytics and own the PII logic.
4. **Effort: Medium–Hard** (you write/deploy Worker glue; no declarative attach point). Gotchas: built-in Guardrails are useless for Korean PII; a Worker runs on the edge, so the self-hosted sidecar must be reachable — use **Cloudflare Tunnel / `cloudflared`** to keep it private, or relocate the sidecar to Cloudflare Containers; **upside:** you fully control fail-closed behavior in the Worker; mind per-invocation CPU/subrequest limits and the double network hop.
5. **Docs:** https://developers.cloudflare.com/ai-gateway/features/guardrails/ · https://developers.cloudflare.com/ai-gateway/features/guardrails/usage-considerations/ · https://developers.cloudflare.com/ai-gateway/integrations/worker-binding-methods/

---

## 4. Kong AI Gateway

1. **What it is.** A suite of `ai-*` plugins on the Kong (OpenResty/Lua) data plane that proxy and govern LLM traffic in front of providers.
2. **Attach mechanism.** The right plugin is **`ai-custom-guardrail`** (**Enterprise-only**): it introspects inbound requests **and** outbound responses by POSTing the body to **any HTTP guardrail service**, parsing the reply with Lua expressions, then block/allow. It extends and requires `ai-proxy`/`ai-proxy-advanced`. OSS fallback: a hand-written custom plugin (Lua/PDK, or Go/JS/Python via the external plugin server) or `pre-function`/`post-function` doing the HTTP callout yourself.
3. **Our integration.** Run the **sidecar** as an upstream; configure `ai-custom-guardrail` declaratively:
   - `config.request` → sidecar URL + a body template mapping the prompt into `{text, policy_profile, scan_stage}` (static fields via `config.params`);
   - `config.response.block` → Lua expr `resp.blocked == true`; `config.response.block_message` → the refusal;
   - `config.functions` → parse `spans`/`masked_text`/`metrics`; `config.metrics` → log into Kong analytics.
   No plugin code needed **if Enterprise**.
4. **Effort: Easy (Enterprise) / Hard (OSS).** Gotchas: the `ai-custom-guardrail` license gate; request/response mapping is Lua expressions, not JSON Schema; it requires `ai-proxy` first (not standalone); **mask-and-forward** (rewriting the forwarded body with `masked_text` rather than only block/allow) is documented around block/allow+metrics and is **[UNVERIFIED]** for body mutation — may need a `pre-function` companion.
5. **Docs:** https://developer.konghq.com/plugins/ai-custom-guardrail/ · https://developer.konghq.com/ai-gateway/ · https://developer.konghq.com/plugins/ai-prompt-guard/

---

## 5. NVIDIA NeMo Guardrails

1. **What it is.** Open-source Python toolkit adding programmable "rails" (input/dialog/output/retrieval/execution) to LLM apps via `config.yml` + Colang flows + `actions.py`.
2. **Attach mechanism.** Register a **custom Python action** (`@action(name=..., execute_async=True)` in `actions.py`, or `LLMRails.register_action(...)`) and wire it into an **input rail** (runs on the user message before the LLM — can reject *or* alter/mask) and an **output rail** (runs on the response) via a Colang flow listed under `rails:`.
3. **Our integration.** Best fit is the **Python library** — call `GuardrailPipeline.process(GuardrailRequest(...))` directly inside the `@action` (no network hop), returning `blocked` and writing `masked_text` back into the context for input rails. (Alternatively `httpx.post` the sidecar for process isolation.) Map input-vs-output rails to `scan_stage`.
4. **Effort: Medium.** The action is trivial; friction is **Colang** (1.x vs 2.0 syntax differs — verify your version). Gotchas: to **mask** you must write the modified message back into context, not just return a bool (mechanism is version-specific); keep the action deterministic/local so it doesn't trigger an unintended extra LLM call; `actions.py` auto-registers only inside the config folder.
5. **Docs:** https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/actions/registering-actions.html · https://docs.nvidia.com/nemo/guardrails/latest/user-guides/python-api.html · https://github.com/NVIDIA-NeMo/Guardrails

---

## 6. Guardrails AI

1. **What it is.** Open-source Python framework where **Validators** compose into **Guards** that intercept LLM inputs/outputs; also ships a **Guardrails Server** exposing guards behind an OpenAI-compatible REST endpoint.
2. **Attach mechanism.** Write a custom `@register_validator` class, override `_validate` (not `validate`), and attach via `Guard().use(KoreanPII, on_fail="fix")`. Runs as Input and/or Output Guards.
3. **Our integration.** Wrap `GuardrailPipeline.process(...)` inside `_validate` (in-process, cleanest). On detection return `FailResult(error_message=..., fix_value=result.masked_text, error_spans=...)`; with `on_fail="fix"` the Guard substitutes the **masked text**. Use the Guard programmatically, or run the Guardrails Server and call it via the OpenAI SDK at `/guards/<name>/openai/v1/`.
4. **Effort: Easy** (cleanest Python-native fit). Gotchas: implement `_validate`, never `validate`; input masking needs `fix_value` **and** `on_fail="fix"`; targeting the input prompt uses an `on=` kwarg on `.use()` whose exact spelling is **[UNVERIFIED]** (confirm in the Guard concept docs); `error_spans` expects offsets into the validated string — map our `spans` accordingly.
5. **Docs:** https://guardrailsai.com/docs/how_to_guides/custom_validators · https://guardrailsai.com/docs/concepts/guard · https://www.guardrailsai.com/docs/concepts/validator_on_fail_actions

---

## 7. Helicone

1. **What it is.** Open-source LLM observability proxy (inline gateway in Rust + an async OpenLLMetry logging mode). Logs requests/responses, cost, tokens; caching, rate limiting, and a built-in LLM Security check.
2. **Attach mechanism.** **No pluggable custom guardrail.** Its inline LLM Security (Meta Prompt Guard + Llama Guard, enabled via `Helicone-LLM-Security-Enabled: true`) can *block* but is **fixed**, prompt-injection-focused, and OpenAI-models-only. Webhooks are **async/observational** — they fire after the fact and cannot block or transform in-flight. Custom Properties are metadata tags, not a control hook. **Helicone entered maintenance mode on 2026-03-03 (no new features).**
3. **Our integration.** **Effectively none, inline.** There is no supported way to have Helicone call `/v1/pii/apply` mid-pipeline and act on `{blocked, masked_text}`. Options are observe-only (stream logs out-of-band) or run our sidecar as a **separate proxy hop** in front of/behind Helicone — Helicone itself won't enforce masking/blocking.
4. **Effort: Hard / effectively N/A** for inline custom guardrailing. Use Helicone for observability and put enforcement elsewhere.
5. **Docs:** https://docs.helicone.ai/gateway/overview · https://docs.helicone.ai/features/advanced-usage/llm-security

---

## 8. MLflow / Databricks (Mosaic / Unity) AI Gateway

1. **What it is.** Databricks' central AI governance layer in front of model/agent/MCP endpoints — analytics, permissions, rate/token limits, and AI Guardrails per serving endpoint. (MLflow's open Deployments/AI Gateway server is the OSS lineage.)
2. **Attach mechanism.** Built-in guardrails include **PII detection** with **redaction** (placeholder substitution) or **blocking** (reject), plus safety/jailbreak. **Custom guardrails (GA 2025)** are **LLM-as-judge evaluators served on Model Serving endpoints** — *not* arbitrary HTTP filters. The gateway sends a chat request and expects `{"flagged": bool, "confidence": float}` (blocking) or `{"flagged": bool, "sanitized_text": str}` (sanitizing).
3. **Our integration.** Indirect. Our `/v1/pii/apply` is not a chat-completions endpoint, so wrap it behind a **Model Serving endpoint speaking the OpenAI Chat Completions schema**: a thin adapter that receives the gateway's chat request, calls `/v1/pii/apply`, and returns `{"flagged": blocked, "sanitized_text": masked_text}`. Must live inside Databricks (no arbitrary external URL).
4. **Effort: Medium–Hard.** It can both block (400) and sanitize in place. Gotchas: repackage our logic as an OpenAI-chat Model Serving endpoint; platform lock-in + serving cost; the rigid `flagged`/`sanitized_text` contract drops our richer `spans`/`metrics`. **Note:** built-in Databricks PII is English/entity-centric — it does **not** cover our Korean text-form PII, which is the gap we fill.
5. **Docs:** https://docs.databricks.com/aws/en/ai-gateway/guardrails · https://www.databricks.com/blog/how-safeguard-ai-workloads-unity-ai-gateway-guardrails

---

## 9. Azure — API Management (APIM) GenAI gateway + AI Content Safety

1. **What it is.** APIM's AI gateway is an inbound/outbound **programmable policy pipeline** layered on the API gateway. Azure AI Content Safety is a separate Cognitive Service for harm-category moderation.
2. **Attach mechanism (best fit of the SaaS gateways).** Two complementary inline policies:
   - **`llm-content-safety`** — sends prompts/completions to Content Safety; blocks with **403** on harmful content (Hate/SelfHarm/Sexual/Violence + `shield-prompt`). Harm categories only — **not general PII**.
   - **`send-request`** (the key one) — a general policy that **calls an arbitrary external HTTP service mid-pipeline**, captures the result into a variable; combined with **`set-body`** + `choose`/`return-response`, you can inspect the verdict and **block (403)** or **transform** the prompt (inject `masked_text`).
3. **Our integration.** Cleanest external-HTTP path of all the SaaS gateways. In the **inbound** policy: `send-request` → `POST https://<sidecar>/v1/pii/apply` (`scan_stage:"request"`) into `piiResponse`; `choose`: if `piiResponse.blocked` → `return-response` 403; else `set-body` to inject `piiResponse.masked_text` and forward. Repeat in **outbound** with `scan_stage:"response"`. Auth via `set-header`/managed identity; set `ignore-error="false"` + `timeout` to **fail closed**.
4. **Effort: Medium.** Full block + transform control. Gotchas: policies are **XML + C# expressions** (parsing/re-serializing the OpenAI `messages` body takes care); `send-request` adds a synchronous hop (handle timeouts explicitly); built-in Azure PII (Content Safety is harm-only; **Azure AI Language PII** is a different, English-centric service) won't catch Korean text-form PII — your sidecar must do all of it; streaming complicates outbound rewriting.
5. **Docs:** https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities · https://learn.microsoft.com/en-us/azure/api-management/llm-content-safety-policy · https://learn.microsoft.com/en-us/azure/api-management/send-request-policy

---

## 10. AWS Bedrock Guardrails (native — and how we complement it)

> **⚠️ Correction to the project's working premise.** The CLAUDE.md assumption that "Bedrock is English-centric and misses Korean PII" is **outdated**. Per the live AWS doc (verified 2026-06-23), **Korean is "Optimized and supported"** (the top tier) for the **sensitive-information (PII) filter**, **content filters**, and **denied topics**. It is **NOT** supported for **contextual grounding** (English/French/Spanish only) or **word filters** (English/French/Spanish). The complement argument must shift from *"can't read Korean"* to *"its black-box ML PII model + static regex still has specific, measurable Korean gaps."*

1. **What it is.** A fully managed, model-independent safety layer (content filters incl. PROMPT_ATTACK, denied topics, word filters, PII/sensitive-info filters with **custom regex**, contextual grounding). **You cannot run custom code inside it.**
2. **Korean / PII specifics.** Built-in PII filter officially works on Korean. Custom regex (`regexesConfig`, BLOCK/ANONYMIZE/NONE, separate input/output) lets you add a **Korean RRN (주민등록번호) pattern natively** — but **lookaround is not supported** (rewrite RRN patterns linearly; 1–500 chars). Contextual grounding has **no Korean** (a real gap for RAG defenses).
3. **`ApplyGuardrail` API** is **standalone** — `source:"INPUT"|"OUTPUT"`, `content:[{text:{text}}]` → `action: GUARDRAIL_INTERVENED|NONE` + per-policy assessments. AWS markets it for multi-provider gateways and pre-flight checks, so a gateway can call **both** `ApplyGuardrail` and our sidecar on the same text.
4. **How we complement Bedrock (revised story).**
   1. **Adversarial Korean normalization** (our strongest differentiator) — Bedrock is a black box you cannot tune for jamo decomposition, zero-width-space injection, NFKC/full-width tricks. Our 13-step normalizer runs **before** Bedrock, defeating the encoding/format mutations behind our 62.8% L2 recovery.
   2. **Korean text/semantic PII Bedrock's taxonomy lacks** — job titles (직급), medical/allergy/surgery, salary (연봉). Our keyword dictionary fills this.
   3. **Korean RRN: hybrid** — add an RRN regex to Bedrock as a native baseline, but our guardrail still wins on **checksum validation + context disambiguation**.
   4. **Defense-in-depth ordering:** `our normalizer + Korean detector` → `ApplyGuardrail` (Bedrock) → LLM.
5. **Effort + gotchas.** Managed, no custom code (complement via pre/post + custom regex). Contextual grounding has no Korean; Standard tier needs cross-Region inference (PII filter is tier-independent); Bedrock **traces/CloudWatch logs contain raw unmasked PII** — keep them out of your no-raw-PII boundary. Cost (per ≤1,000-char unit): content $0.15, denied-topics $0.15, PII $0.10, grounding $0.10; word filters + PII regex free. Available in **ap-northeast-2 (Seoul)**.
6. **Docs:** https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-supported-languages.html · https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-sensitive-filters.html · https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-independent-api.html

> **Action item for the paper:** the old "Bedrock can't read Korean" claim is **refuted**. The defensible thesis is now an empirical A/B — **Bedrock-native Korean PII vs Bedrock + our Layer 0** on the 8,400-case fuzzer. Managed ML detectors often lag on agglutinative/text-form Korean PII and adversarial mutations; *measuring* that gap is the new contribution.

---

## 11. Generic fallback — OpenAI-compatible reverse proxy / sidecar HTTP filter

For any gateway with no usable hook (or to stay gateway-agnostic), wrap the guardrail as its own hop. Two forms:

- **Sidecar HTTP filter (what we already have):** the `/v1/pii/apply` service. Any gateway that can call an external HTTP endpoint mid-pipeline (Azure APIM `send-request`, Kong `ai-custom-guardrail`, Portkey webhook, a Cloudflare Worker, a custom LiteLLM hook) targets this. This is the **reusable core** — write the sidecar once; each gateway only needs a thin adapter.
- **OpenAI-compatible reverse proxy:** a thin `POST /v1/chat/completions` server that (1) extracts messages, (2) calls `/v1/pii/apply` (`scan_stage:"input"`) — block or replace with `masked_text`, (3) forwards to the real upstream (any OpenAI-compatible endpoint or another gateway), (4) re-scans the completion (`scan_stage:"output"`), (5) returns. Point any OpenAI SDK / app at it by changing `base_url`. **Maximally portable** (works in front of *every* provider/gateway, no vendor hook needed); costs you one extra network hop and you must handle streaming (SSE) and auth pass-through.

**Reusable-design takeaway:** keep the guardrail as **one OpenAI-compatible / simple HTTP `/guardrail` sidecar that multiple gateways call.** The expensive parts (NER model, normalizer, dictionaries, no-raw-PII contract, fail-closed policy) live once in the sidecar; each gateway integration is a ~30–80-line adapter translating that gateway's hook schema to `{text, policy_profile, scan_stage}` ⇄ `{blocked, masked_text, spans}`. This is exactly how our LiteLLM hook is already built and should be the template for all others.

---

## 12. Comparison table

| Gateway / Framework | Custom-guardrail attach mechanism | Our integration pattern | Calls external HTTP sidecar? | Block + Mask? | Effort |
|---|---|---|---|---|---|
| **LiteLLM** | `CustomGuardrail` subclass (`async_pre_call_hook` / `async_post_call_success_hook` / `apply_guardrail`) | **Sidecar** via `httpx` hook (built) | Yes | Both | **Easy (done)** |
| **Portkey** | Native **Webhook guardrail** (BYO Guardrails), `eventType` before/after | **Sidecar** + schema adapter endpoint | Yes (public URL / self-host OSS) | Both (`transformedData`) | **Easy–Medium** |
| **Cloudflare AI Gateway** | No native hook; **Workers** (`env.AI` + `fetch`) | **Worker** middleware → sidecar (via Tunnel) | Yes (edge → tunnel) | Both (you build it) | **Medium–Hard** |
| **Kong AI Gateway** | `ai-custom-guardrail` plugin (Enterprise) → HTTP callout; OSS = custom Lua/Go plugin | **Sidecar** via declarative plugin config | Yes | Block native; mask **[UNVERIFIED]** | **Easy (Ent) / Hard (OSS)** |
| **NeMo Guardrails** | Custom `@action` wired into Colang input/output rails | **Library** in-process (or sidecar) | Optional | Both (write back to context) | **Medium** (Colang) |
| **Guardrails AI** | Custom `Validator` (`@register_validator`) via `Guard().use()` | **Library** in `_validate` (or sidecar) | Optional | Both (`fix_value` + `on_fail="fix"`) | **Easy** |
| **Helicone** | None pluggable (built-in security only; webhooks async) | Observe-only / separate proxy hop | No (inline) | Neither (inline) | **Hard / N/A** |
| **Databricks/Mosaic AI Gateway** | Custom guardrail = LLM-judge **Model Serving** endpoint (chat schema) | Sidecar wrapped as OpenAI-chat serving endpoint | No (in-platform only) | Both (`flagged`/`sanitized_text`) | **Medium–Hard** |
| **Azure APIM + Content Safety** | `send-request` + `set-body` policies (Content Safety = harm only) | **Sidecar** via `send-request` policy | **Yes (best external-HTTP fit)** | Both (403 + `set-body`) | **Medium** |
| **AWS Bedrock Guardrails** | Native managed (no custom code); custom **regex** only | Run **alongside** via `ApplyGuardrail`; we pre-normalize | N/A (we complement) | Native both (Korean PII + regex) | **Medium** (complement) |
| **Generic OpenAI-compat proxy** | — (we *are* the proxy/sidecar) | **Sidecar** + reverse proxy; point `base_url` at us | Yes | Both | **Easy–Medium** |

---

## 13. Recommended priority for a *Korean* PII guardrail

Ranked by value-for-effort, given our sidecar already exists and our differentiator is Korean-adversarial + text-form PII:

1. **LiteLLM** — already integrated; the reference and the place to demo. *(done)*
2. **Generic OpenAI-compatible reverse-proxy sidecar** — build this next. One artifact makes us deployable in front of *any* provider/gateway with zero vendor lock-in; it's the portable backbone of everything else.
3. **Portkey** — lowest-effort *native* third-party integration (purpose-built webhook, input+output, returns masked text). Strong capstone breadth with a ~50-line adapter. Mind its fail-open default.
4. **Azure APIM** — best path if an enterprise/Azure reviewer matters: the only major SaaS gateway with a clean, supported "call an external HTTP filter and act on its verdict" policy, fail-closeable.
5. **Guardrails AI** — easiest *framework* integration and a credible OSS ecosystem citation; embeds our library directly, no network hop.
6. **AWS Bedrock (complement)** — high research value: the **Bedrock-native-Korean vs Bedrock+ours** A/B is now the sharpest experiment (replacing the refuted "no Korean" claim). Medium effort, big paper payoff.
7. **NeMo Guardrails** — solid OSS citation; in-process library fit; Colang is the only friction.
8. **Kong AI Gateway** — compelling *if* you have Enterprise (declarative HTTP callout); otherwise OSS custom-plugin work is disproportionate for a capstone.
9. **Cloudflare AI Gateway** — only via a Worker + Tunnel; built-in Guardrails exclude Korean. Do only if edge deployment is a goal.
10. **Databricks/Mosaic** — only if already on Databricks; requires repackaging as a serving endpoint.
11. **Helicone** — observability companion, **not** an enforcement point (maintenance mode). Skip for guardrailing.

---

## 14. Cross-cutting findings & flags

- **None of the built-in PII features cover Korean *text-form* PII** (Databricks, Azure AI Language, Cloudflare/Llama Guard). Bedrock's PII filter *does* support Korean as of 2026 — but as an untunable black box vulnerable to adversarial normalization. This is precisely the gap our guardrail fills, and it holds across every platform.
- **Fail-open is the industry default** (Portkey timeout→pass; most gateways). Our contract is **fail-closed** — re-assert it explicitly in *every* integration (Portkey: sync+DENY + tight timeout; APIM: `ignore-error="false"`; Cloudflare/Kong: in your own code).
- **Raw-PII leakage at the gateway boundary** is the recurring risk: gateway access logs / Bedrock traces / Cloudflare analytics can capture the *original* prompt. Keep raw request/response logging off or redacted wherever the gateway sits in front of the sidecar.
- **One sidecar, many adapters** is the correct architecture: expensive logic once; thin per-gateway schema translators.

**Explicitly flagged as uncertain:** Kong `ai-custom-guardrail` body-mutation/mask-and-forward; Guardrails AI exact `on=` input-targeting kwarg; Portkey enterprise private-network webhook config; the NeMo Colang version-specific message-rewrite mechanism. Verify these against the linked docs before committing those specific integrations.

---

### Source index (primary)
LiteLLM: docs.litellm.ai/docs/proxy/guardrails · Portkey: portkey.ai/docs/product/guardrails · Cloudflare: developers.cloudflare.com/ai-gateway/features/guardrails · Kong: developer.konghq.com/plugins/ai-custom-guardrail · NeMo: docs.nvidia.com/nemo/guardrails · Guardrails AI: guardrailsai.com/docs · Helicone: docs.helicone.ai · Databricks: docs.databricks.com/aws/en/ai-gateway/guardrails · Azure: learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities · Bedrock: docs.aws.amazon.com/bedrock/latest/userguide/guardrails-supported-languages.html
