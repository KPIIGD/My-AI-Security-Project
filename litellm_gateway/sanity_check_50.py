"""
Sanity check — re-run 50 sampled cases through the LiteLLM gateway
and compare action/output against the stored 4/16 results.

If new == old in >90% of cases, eval_full.json is still trustworthy
as a baseline (gateway/guardrails behavior unchanged).
"""
import asyncio
import json
import random
import sys
import time
import httpx

sys.stdout.reconfigure(encoding="utf-8")

INPUT = "eval_full.json"
LITELLM_BASE = "http://localhost:4000"
LITELLM_KEY = "sk-1234"
LAYERS = ["Presidio PII", "Bedrock Guardrail", "Lakera"]
SAMPLE_SIZE = 50
SEED = 42


async def call_guardrail(client, name, text):
    start = time.time()
    try:
        r = await client.post(
            f"{LITELLM_BASE}/guardrails/apply_guardrail",
            headers={"Authorization": f"Bearer {LITELLM_KEY}", "Content-Type": "application/json"},
            json={"guardrail_name": name, "text": text},
            timeout=60.0,
        )
        lat = int((time.time() - start) * 1000)
        if r.status_code == 500:
            try:
                detail = r.json().get("detail", "")
            except Exception:
                detail = ""
            return {"action": "BLOCK", "output": "[BLOCKED]", "detail": str(detail)[:200], "latency_ms": lat, "status": 500}
        elif r.status_code == 400:
            try:
                detail = r.json().get("error", {}).get("message", r.text[:200])
            except Exception:
                detail = r.text[:200]
            return {"action": "BLOCK", "output": "[BLOCKED]", "detail": str(detail)[:200], "latency_ms": lat, "status": 400}
        elif r.status_code == 200:
            data = r.json()
            output = data.get("response_text", text)
            return {"action": "MASK" if output != text else "PASS", "output": output, "detail": None, "latency_ms": lat, "status": 200}
        else:
            return {"action": "ERROR", "output": text, "detail": f"HTTP {r.status_code}", "latency_ms": lat, "status": r.status_code}
    except Exception as e:
        return {"action": "ERROR", "output": text, "detail": str(e)[:200], "latency_ms": int((time.time() - start) * 1000), "status": -1}


async def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data["results"]

    random.seed(SEED)
    sample = random.sample(cases, SAMPLE_SIZE)

    print(f"Sanity check: {SAMPLE_SIZE} cases (seed={SEED}) against {LITELLM_BASE}\n")

    matches = {l: 0 for l in LAYERS}
    differs = {l: [] for l in LAYERS}
    new_errors = {l: 0 for l in LAYERS}

    async with httpx.AsyncClient() as client:
        for i, case in enumerate(sample, 1):
            text = case.get("mutated", "")
            old_lr = {lr["layer"]: lr for lr in case.get("layer_results", [])}

            print(f"[{i:2}/{SAMPLE_SIZE}] {case.get('pii_type','?'):14} {case.get('mutation_name','?'):14} L{case.get('mutation_level','?')} ", end="", flush=True)

            for layer in LAYERS:
                new = await call_guardrail(client, layer, text)
                old = old_lr.get(layer, {})
                old_action = old.get("action", "?")
                new_action = new["action"]

                if new["action"] == "ERROR":
                    new_errors[layer] += 1
                    print(f"  {layer[:8]:8}=ERR", end="")
                elif old_action == new_action:
                    matches[layer] += 1
                    print(f"  {layer[:8]:8}=OK ", end="")
                else:
                    differs[layer].append({
                        "id": case.get("id"),
                        "pii_type": case.get("pii_type"),
                        "mutation": case.get("mutation_name"),
                        "old": old_action,
                        "new": new_action,
                        "old_output": str(old.get("output", ""))[:60],
                        "new_output": str(new["output"])[:60],
                    })
                    print(f"  {layer[:8]:8}=DIFF({old_action}->{new_action})", end="")
            print()

    print("\n" + "=" * 72)
    print("  SANITY CHECK SUMMARY")
    print("=" * 72)
    for layer in LAYERS:
        m = matches[layer]
        d = len(differs[layer])
        e = new_errors[layer]
        total = m + d + e
        print(f"  {layer:20s}  match={m}/{total}  ({100*m/total:.1f}%)  differ={d}  err={e}")

    for layer in LAYERS:
        if differs[layer]:
            print(f"\n--- {layer} discrepancies (first 5) ---")
            for d in differs[layer][:5]:
                print(f"  {d['pii_type']:12} {d['mutation']:14} {d['old']:6}->{d['new']:6}")
                print(f"    old_out: {d['old_output']!r}")
                print(f"    new_out: {d['new_output']!r}")


if __name__ == "__main__":
    asyncio.run(main())
