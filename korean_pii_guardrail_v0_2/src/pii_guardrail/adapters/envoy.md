# Envoy — attach the Korean PII guardrail

Envoy is honest about its limits here, so read the two options carefully.

## Option A — Mask + block (recommended): route through our reverse proxy

Envoy can't easily rewrite a JSON body inline, so for **masking** put our
reverse proxy in the data path as an upstream cluster:

```
client → Envoy → cluster: pii_reverse_proxy → real LLM
```

```yaml
# the reverse proxy (masks in & out) is just another Envoy cluster
clusters:
  - name: pii_reverse_proxy
    type: STRICT_DNS
    load_assignment:
      cluster_name: pii_reverse_proxy
      endpoints:
        - lb_endpoints:
            - endpoint:
                address: { socket_address: { address: pii-reverse-proxy, port_value: 8000 } }
```
Run it: `OPENAI_BASE_URL=https://api.openai.com/v1 uvicorn pii_guardrail.adapters.reverse_proxy:app --port 8000`

## Option B — Block-only via ext_authz (no masking)

The `ext_authz` HTTP filter can call an external service that returns
allow/deny, so it can **block** requests containing high-risk PII, but it
**cannot mask** the body (ext_authz only allows/denies + adds headers). Inline
body mutation needs `ext_proc` (gRPC), which our HTTP sidecar does not speak.

```yaml
http_filters:
  - name: envoy.filters.http.ext_authz
    typed_config:
      "@type": type.googleapis.com/envoy.extensions.filters.http.ext_authz.v3.ExtAuthz
      transport_api_version: V3
      with_request_body: { max_request_bytes: 65536, allow_partial_message: false }
      failure_mode_allow: false        # fail-closed: deny if the checker is down
      http_service:
        server_uri:
          uri: http://pii-authz:8090
          cluster: pii_authz
          timeout: 2s
        authorization_request:
          headers_to_add: [{ key: "content-type", value: "application/json" }]
```

Provide a tiny "authorize" endpoint that scans the buffered body and returns
200 (allow) / 403 (deny) — for example a FastAPI route that calls
`pii_guardrail.adapters.core.scan(...)` and returns 403 when `blocked` or when
any high-risk span is found. (ext_authz can't return the masked text, so use
Option A when you need masking.)

> Verification: tested-by-inspection artifact (no live Envoy here). Option A
> reuses the reverse proxy, which IS run-verified.
