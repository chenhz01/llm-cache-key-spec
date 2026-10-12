# llm-cache-key-spec

llm-cache-key-spec turns LLM request payloads into stable cache keys: Unicode NFC normalization, volatile-field stripping, recursive key sorting, whitespace collapse, canonical JSON, then a namespaced SHA-256 digest. Same logical request → same key, regardless of key order or stray whitespace. Use it to make prompt caching reproducible and collision-auditable. Confidence: High (≥80%) for stability under the documented normalizations, per the 61-check suite.

## Problem

Prompt/response caches miss for stupid reasons: JSON objects serialized with different key order, a user's request carrying `session_id` or `timestamp` fields, double vs single spaces in a prompt, `1.0` vs `1`. Every miss is a paid model call. Worse, teams rarely test their cache keys for collisions at all. What is needed is one normalization spec + one digest function + a collision tester you can run over your corpus.

## How it works

Pipeline (all pure stdlib):

1. **Strip volatile fields** — recursively removes named keys (e.g. `session_id`, `timestamp`) anywhere in the payload tree.
2. **Normalize strings** — Unicode NFC, then whitespace collapse on every string in the tree.
3. **Canonicalize** — floats that are integral and < 2⁵³ become ints; JSON serialized with `sort_keys=True`, compact separators, `ensure_ascii=False`.
4. **Digest** — SHA-256 over a namespaced material block `{"v": "llmk1", "ns", "model", "params", "body"}`; key format `llmk1:<ns>:<hex>`.
5. **Collision tooling** — `collision_test(keys)` reports duplicates in a corpus; `birthday_estimate(n)` gives the exact birthday-bound probability for n uniform 256-bit keys.

The `model` and `params` inputs are bound into the material, so temperature changes invalidate by design; `v` (`llmk1`) lets you bump the whole keyspace when the spec evolves.

## Quickstart (~3 min)

```bash
# step 1: key a payload file (~1 s)
python cachekey.py key request.json --ns myapp --model gpt-x --volatile session_id,ts
# step 2: bind sampling params explicitly
python cachekey.py key request.json --params '{"temperature":0.7}'
# step 3: audit a corpus of keys for collisions
python cachekey.py collide keys.jsonl
# full suite (~3 s)
python self_test.py   # SUMMARY: PASS 61/61 [Measured]
```

Library use: `compute_key(payload, namespace, model, params, volatile)` and `collision_test(keys)`.

## Why not X? (as of 2026-10-12)

- **Jdawgboo/semantic-cache-key** — "Create normalized, stable SHA-256 cache keys for AI request inputs." Same goal, TypeScript ecosystem; this repo is the Python/stdlib line with a published normalization *spec* (NFC → strip → sort → collapse → canonical JSON) plus the collision-test and birthday-bound tooling in the same package.
- **MukundaKatta/semantic-cache-key-py** — "Python port of @mukundakatta/semantic-cache-key: stable cache keys for AI prompts." A port of the same idea; this repo differs by binding model + sampling params + a spec version (`llmk1`) into the key material so cache invalidation is explicit rather than ad hoc.
- **bobbyhalljr/llm-cache-key** — "A TypeScript fixture for scoped, versioned LLM result caching. Sixteen checks, no model call." A fixture-style test harness for scoped caching; this repo ships the generator and collision auditor themselves, not only the checks.

## Minimal Fallback (PLAN B)

No Python? One jq line catches the biggest miss source: `jq -S -c . request.json | sha256sum` (recursive key sort + digest). You lose volatile-field stripping, Unicode NFC, whitespace collapse, and float canonicalization — so expect misses on payloads that differ only in those, and never feed unsanitized user fields into it.

## Design Trade-offs

Priority order: **stability > explicit invalidation > collision-auditability > speed**. Whitespace collapse and NFC make keys robust to presentation noise but mean "different" prompts (different indentation, composed vs decomposed accents) share an entry — accepted, because such differences never change model semantics [assumed, see Core Assumptions]. Namespacing via `ns` + `model` + `params` in the material trades longer key strings for instant tenant/model/temperature isolation without hashing surprises. `float→int` coercion applies only below 2⁵³, where integers are exact.

## Limits & Second-order Effects

- Semantics-blind: "cache the result for me" and "cache the result 4 me" are different keys (different tokens) — no fuzzy/semantic caching here.
- Volatile-field stripping is name-based: strip `timestamp` and you also strip a legitimate field named `timestamp` inside a nested object.
- Whitespace inside strings is collapsed everywhere, including inside quoted content where formatting might matter (code prompts: do not collapse; pass raw and strip only metadata fields).
- Second-order: stable keys + long TTLs silently serve stale answers after prompt-template updates unless the template version is part of the payload or the namespace. Version your prompts into the key material.
- A collision-free corpus audit is necessary, not sufficient — SHA-256 collisions are not the realistic failure mode; forgotten volatile fields are.

## FAQ

**Why not just hash the raw JSON?** Because two logically identical requests serialize differently — key order, float format, whitespace — and every difference is a paid cache miss.

**What is `llmk1` for?** A spec version baked into the key: when normalization rules change, bump it and the old cache is invalidated wholesale instead of half-matching.

### When NOT to use this tool?

- You want semantic caching (similar prompts share entries) — this is exact-match by design.
- Your payloads contain large raw files/blobs — hash those separately and reference them.
- You need cross-language byte-identical keys with another implementation — pin the spec yourself; float/Unicode edge cases can diverge.
- Prompt formatting is meaningful (code generation with whitespace-sensitive prompts) — collapse normalization is wrong for you.

## License

MIT — see `LICENSE`. Contact: hcac4735@agent.qq.com

---

[Core Assumptions]
- Whitespace and Unicode composition differences in prompts do not change model semantics enough to justify separate cache entries.
- Volatile fields are enumerable per application; the caller supplies the correct strip list.
- Sampling params and model identity must invalidate the key (they are bound into the material, not the payload).
- SHA-256 collision probability is negligible for realistic corpus sizes; collision testing guards against implementation bugs, not cryptography, as of 2026-10-12.

---

Part of the [zhengming-toolbox](https://github.com/chenhz01/zhengming-toolbox) — 55 purpose-built AI-engineering tools across neglected niches.

Related tools: [fewshot-picker-bench](https://github.com/chenhz01/fewshot-picker-bench) · [instruction-dsl-lint](https://github.com/chenhz01/instruction-dsl-lint) · [prompt-regression-harness](https://github.com/chenhz01/prompt-regression-harness)
