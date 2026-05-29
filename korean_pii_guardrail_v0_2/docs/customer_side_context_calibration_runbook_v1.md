# Customer-Side Context Calibration Runbook v1

Run evidence collection inside the customer environment and export aggregates only.

Required controls:

- Use a versioned scoring config id.
- Hash deployment identifiers before export.
- Export counts by domain, rule id, entity type, action, and optional review outcome.
- Suppress small-count rows below the configured threshold.
- Do not export raw text, raw URLs, span text, candidate values, or reversible maps.
- Treat received aggregates as evidence for review, not automatic score changes.

Small-count threshold: `10`

Central analysis may consume only the JSON template fields in the companion report.
