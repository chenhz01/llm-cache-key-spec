# Alignment Audit (Rules 85-100 / 16 items) — llm-cache-key-spec v0.1.1

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Safety/Ethics section | N/A | Not a security-research repo; no dual-use surface; fails closed (exit 2) on unreadable payload/params and rejects `payload=None` with TypeError |
| 2 | Privacy/dezero | PASS | No secrets/tokens/real names in any file; only contact line uses hcac4735@agent.qq.com (README License section); grep `(sk-\|ghp_\|api[_-]?key\s*=\s*['"][A-Za-z0-9])` → 0 hits |
| 3 | Copyright boundary | PASS | semantic-cache-key (TS), semantic-cache-key-py, llm-cache-key comparisons are structural restatements of their public descriptions, no >50-char copied text; MIT LICENSE present, "zhengming contributors" |
| 4 | Fact-check annotation | PASS | 61-check suite "~3 s" marked [Measured] with repro `python self_test.py`; other timings ~; collision claims tied to SHA-256 birthday bound (computed, not estimated) |
| 5 | Confidence grading | PASS | Opener stability claim [High ≥80%] tied to the suite; whitespace-independence marked [assumed] in Trade-offs with pointer to Core Assumptions; ≥2 explicit labels |
| 6 | PLAN B built-in | PASS | "Minimal Fallback (PLAN B)" section: single `jq -S -c . \| sha256sum` pipeline with explicit losses listed |
| 7 | Timeout preset | PASS | Quickstart states "~3 min" with ~1 s / ~3 s step markers |
| 8 | Rule-conflict arbitration | PASS | "Design Trade-offs" opens with priority order: stability > explicit invalidation > collision-auditability > speed |
| 9 | Version changelog | PASS | CHANGELOG.md v0.1.0 + v0.1.1; v0.1.1 records documentation completion and suite re-verification |
| 10 | Exemption instruction | N/A | Session-level rule; static repo content not applicable |
| 11 | External-knowledge cutoff | PASS | why-not-X comparisons and equivalence claims dated "as of 2026-10-12" |
| 12 | Assumption explicitness | PASS | "[Core Assumptions]" section with 4 items |
| 13 | Logic-check trio | PASS | self_test.py three-tier suite (functional / error / extreme-edge, incl. unicode NFC, float coercion boundaries, collision corpus); `python self_test.py` → `SUMMARY: PASS 61/61` |
| 14 | Socratic question | PASS | FAQ "When NOT to use this tool?" with 4 anti-use-cases (semantic caching, large blobs, cross-language byte-identity, whitespace-sensitive prompts) |
| 15 | Pareto improvement | PASS | v0.1.1 documentation round: README documents the material-block layout (v/ns/model/params/body), PLAN B, and stale-cache second-order risks absent from the module docstring; traceable in CHANGELOG |
| 16 | Ultimate fallback (≤60-word opener) | PASS | First paragraph = 59 words, contains what-it-is and the "Same logical request → same key" judgment sentence |

Second-order effects (rule 16 bonus): PASS — "Limits & Second-order Effects" covers stale-answer serving after template updates, name-based over-stripping, and misdirected collision anxiety.

Scan evidence: `grep -rEn "(sk-|ghp_|api[_-]?key\s*=\s*['\"][A-Za-z0-9])" .` → 0 hits; `grep -rn "hcac4735@agent.qq.com" README.md` → 1 hit.
