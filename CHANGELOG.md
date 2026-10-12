# Changelog

## v0.1.1 — 2026-10-12
- Documentation layer completed: README (Problem / How it works / Quickstart / why-not-X anchored on the two semantic-cache-key repos and llm-cache-key / Minimal Fallback / Trade-offs / Limits / FAQ), ALIGNMENT.md 16-item audit.
- Self-test re-verified green, no code changes needed this round: `python self_test.py` → `SUMMARY: PASS 61/61`.

## v0.1.0 — 2026-10-11
- Initial implementation: volatile-field stripping (recursive), NFC + whitespace-collapse string normalization, integral-float canonicalization, canonical JSON with sorted keys, namespaced `llmk1` SHA-256 key material (ns/model/params binding), `collision_test` corpus auditor with birthday-bound estimate, CLI (`key` / `collide` subcommands, `--volatile`, `--json`, exit 2 on bad input).
- Self-test suite (functional / error / extreme-edge tiers).
