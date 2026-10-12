#!/usr/bin/env python3
"""llm-cache-key-spec — spec + implementation for stable LLM cache keys.

Pipeline: unicode NFC -> volatile-field stripping -> recursive key sort ->
whitespace collapse -> canonical JSON -> SHA-256 namespaced digest.
Pure stdlib.
"""
import argparse
import hashlib
import json
import sys
import unicodedata

KEY_VERSION = "llmk1"


def strip_fields(obj, volatile):
    """Remove volatile fields recursively (dict keys anywhere in the tree)."""
    if isinstance(obj, dict):
        return {k: strip_fields(v, volatile) for k, v in obj.items() if k not in volatile}
    if isinstance(obj, list):
        return [strip_fields(v, volatile) for v in obj]
    return obj


def normalize_text(s):
    s = unicodedata.normalize("NFC", s)
    return " ".join(s.split())


def _norm_strings(obj):
    if isinstance(obj, str):
        return normalize_text(obj)
    if isinstance(obj, dict):
        return {k: _norm_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_norm_strings(v) for v in obj]
    if isinstance(obj, float) and obj.is_integer() and abs(obj) < 2 ** 53:
        return int(obj)
    return obj


def canonicalize(obj, volatile=()):
    """Return the canonical string form used for hashing."""
    obj = strip_fields(obj, set(volatile))
    obj = _norm_strings(obj)
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def compute_key(payload, namespace="default", model=None, params=None, volatile=()):
    """Stable cache key. Identical logical payloads -> identical key."""
    if payload is None:
        raise TypeError("payload must not be None")
    body = canonicalize(payload, volatile)
    material = {
        "v": KEY_VERSION,
        "ns": namespace,
        "model": model,
        "params": canonicalize(params if params is not None else {}, volatile),
        "body": body,
    }
    digest = hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return "%s:%s:%s" % (KEY_VERSION, namespace, digest)


def collision_test(keys):
    """Report duplicate keys in a corpus."""
    seen = {}
    for k in keys:
        seen[k] = seen.get(k, 0) + 1
    collisions = {k: c for k, c in seen.items() if c > 1}
    return {
        "total": len(keys),
        "unique": len(seen),
        "collisions": len(collisions),
        "collision_keys": sorted(collisions.keys())[:20],
    }


def birthday_estimate(n):
    """Estimated collision probability for n uniformly random 256-bit keys."""
    if n < 2:
        return 0.0
    import math
    ln = n * (n - 1) / 2.0 * -math.log(2) / (2 ** 256)
    return -math.expm1(ln)  # expm1 keeps precision for astronomically small probabilities


def main(argv=None):
    ap = argparse.ArgumentParser(prog="llm-cache-key-spec", description="Generate stable, normalized LLM cache keys; test a key corpus for collisions.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_key = sub.add_parser("key", help="compute a cache key for a request JSON file")
    p_key.add_argument("file", help="JSON file with the prompt payload")
    p_key.add_argument("--ns", default="default", help="namespace (e.g. app or tenant)")
    p_key.add_argument("--model", default=None, help="model identifier to bind into the key")
    p_key.add_argument("--params", default=None, help="JSON string of sampling params to bind")
    p_key.add_argument("--volatile", default="", help="comma-separated field names to strip before hashing")
    p_key.add_argument("--json", action="store_true")

    p_col = sub.add_parser("collide", help="collision-test a JSONL corpus of keys (one key string per line)")
    p_col.add_argument("file", help="JSONL file, one key per line")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "key":
            with open(args.file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            params = json.loads(args.params) if args.params else None
            volatile = [v.strip() for v in args.volatile.split(",") if v.strip()]
            key = compute_key(payload, args.ns, args.model, params, volatile)
            if args.json:
                print(json.dumps({"key": key, "ns": args.ns, "model": args.model}, ensure_ascii=False))
            else:
                print(key)
            return 0
        if args.cmd == "collide":
            keys = []
            with open(args.file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        keys.append(line)
            report = collision_test(keys)
            report["birthday_bound_256bit"] = birthday_estimate(len(keys))
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
    except (OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
