#!/usr/bin/env python3
"""self_test.py for llm-cache-key-spec — [A] functional / [B] exception paths / [C] extreme edges."""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cachekey  # noqa: E402

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, False))
        print("  [FAIL] %s -> %r" % (name, e))


def assert_eq(a, b, msg=""):
    assert a == b, msg or "%r != %r" % (a, b)


def assert_true(c, m=""):
    assert c, m


# ---------- [A] functional ----------
def a01():
    k1 = cachekey.compute_key({"prompt": "hello world"})
    k2 = cachekey.compute_key({"prompt": "hello  world"})
    assert_eq(k1, k2, "whitespace collapse")
def a02():
    k1 = cachekey.compute_key({"prompt": "hi"})
    k2 = cachekey.compute_key({"prompt": "hi", "ignored": 1})
    assert_true(k1 != k2, "different payloads -> different keys")
def a03():
    k1 = cachekey.compute_key({"b": 1, "a": 2})
    k2 = cachekey.compute_key({"a": 2, "b": 1})
    assert_eq(k1, k2, "key order must not matter")
def a04():
    k1 = cachekey.compute_key({"p": "caf\u00e9"}, )
    k2 = cachekey.compute_key({"p": "cafe\u0301"})
    assert_eq(k1, k2, "NFC normalization")
def a05():
    v = ("temperature", "seed")
    k1 = cachekey.compute_key({"prompt": "x", "temperature": 0.7}, volatile=v)
    k2 = cachekey.compute_key({"prompt": "x"}, volatile=v)
    assert_eq(k1, k2, "volatile fields stripped")
def a06():
    k1 = cachekey.compute_key({"prompt": "x"}, model="m-a")
    k2 = cachekey.compute_key({"prompt": "x"}, model="m-b")
    assert_true(k1 != k2)
def a07():
    k1 = cachekey.compute_key({"prompt": "x"}, namespace="app1")
    k2 = cachekey.compute_key({"prompt": "x"}, namespace="app2")
    assert_true(k1 != k2 and k1.startswith("llmk1:app1:"))
def a08():
    k = cachekey.compute_key({"prompt": "x"})
    assert_true(k.startswith("llmk1:") and len(k) == len("llmk1:default:") + 64)
def a09():
    k1 = cachekey.compute_key({"prompt": "x"}, params={"t": 0})
    k2 = cachekey.compute_key({"prompt": "x"}, params={"t": 0.0})
    assert_eq(k1, k2, "params canonicalized (0 == 0.0 textually)")
def a10():
    k1 = cachekey.compute_key({"prompt": "x", "meta": {"ts": 1, "id": 2}}, volatile=("ts", "id"))
    k2 = cachekey.compute_key({"prompt": "x", "meta": {}}, volatile=("ts", "id"))
    assert_eq(k1, k2, "volatile fields stripped at any depth")
def a11():
    r = cachekey.collision_test(["a", "a", "b"])
    assert_eq(r["collisions"], 1)
def a12():
    r = cachekey.collision_test([])
    assert_eq((r["total"], r["unique"], r["collisions"]), (0, 0, 0))
def a13():
    r = cachekey.collision_test(["x"] * 100)
    assert_eq(r["unique"], 1)
def a14():
    keys = [cachekey.compute_key({"prompt": "p%d" % i}) for i in range(200)]
    r = cachekey.collision_test(keys)
    assert_eq(r["collisions"], 0)
def a15():
    assert_true(cachekey.birthday_estimate(0) == 0.0 and cachekey.birthday_estimate(1) == 0.0)
def a16():
    assert_true(cachekey.birthday_estimate(10 ** 9) < 1e-50, "256-bit birthday bound tiny at practical scale")
def a17():
    c = cachekey.canonicalize({"z": 1, "a": [2, 1]})
    assert_true(c.index('"a"') < c.index('"z"'))
def a18():
    assert_eq(cachekey.canonicalize("  spaced   out  "), '"spaced out"')
def a19():
    assert_eq(cachekey.canonicalize({"k": "caf\u00e9"}), '{"k":"caf\u00e9"}')
def a20():
    k1 = cachekey.compute_key({"p": "\u4e2d\u6587"})
    k2 = cachekey.compute_key({"p": "\u4e2d\u6587"})
    assert_eq(k1, k2)
def a21():
    here = os.path.dirname(os.path.abspath(__file__))
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        open(path, "w", encoding="utf-8").write('{"prompt": "hi there"}')
        code = subprocess.run([sys.executable, os.path.join(here, "cachekey.py"), "key", path], capture_output=True, text=True)
        assert_eq(code.returncode, 0)
        assert_true(code.stdout.strip().startswith("llmk1:"))
    finally:
        os.unlink(path)
def a22():
    k1 = cachekey.compute_key({"p": "same"})
    k2 = cachekey.compute_key({"p": "same"})
    assert_eq(k1, k2, "deterministic across calls")
def a23():
    r = cachekey.collision_test(["only"])
    assert_eq(r["unique"], 1)

# ---------- [B] exception paths ----------
def b01():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cachekey.py"), "key", "missing.json"], capture_output=True, text=True)
    assert_eq(code.returncode, 2)
def b02():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cachekey.py"), "collide", "missing.jsonl"], capture_output=True, text=True)
    assert_eq(code.returncode, 2)
def b03():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cachekey.py")], capture_output=True, text=True)
    assert_eq(code.returncode, 2)
def b04():
    here = os.path.dirname(os.path.abspath(__file__))
    code = subprocess.run([sys.executable, os.path.join(here, "cachekey.py"), "key", "--help"], capture_output=True, text=True)
    assert_eq(code.returncode, 0)
def b05():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        open(path, "w", encoding="utf-8").write("{broken")
        code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cachekey.py"), "key", path], capture_output=True, text=True)
        assert_eq(code.returncode, 2)
    finally:
        os.unlink(path)
def b06():
    try:
        cachekey.compute_key(None)
        assert False
    except (TypeError, ValueError):
        pass
def b07():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        open(path, "w", encoding="utf-8").write('{"prompt": "x"}')
        code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cachekey.py"), "key", path, "--params", "{bad"], capture_output=True, text=True)
        assert_eq(code.returncode, 2)
    finally:
        os.unlink(path)
def b08():
    assert_eq(cachekey.strip_fields({"a": 1, "b": {"a": 2, "c": 3}}, ("a",)), {"b": {"c": 3}})
def b09():
    r = cachekey.collision_test([""])
    assert_eq(r["total"], 1)
def b10():
    here = os.path.dirname(os.path.abspath(__file__))
    code = subprocess.run([sys.executable, os.path.join(here, "cachekey.py"), "bogus-cmd"], capture_output=True, text=True)
    assert_eq(code.returncode, 2)

# ---------- [C] extreme edges ----------
def c01():
    k1 = cachekey.compute_key({})
    k2 = cachekey.compute_key({})
    assert_eq(k1, k2)
def c02():
    k = cachekey.compute_key({"p": ""})
    assert_true(k.startswith("llmk1:"))
def c03():
    k1 = cachekey.compute_key({"p": "\U0001f680" * 10})
    k2 = cachekey.compute_key({"p": "\U0001f680" * 10})
    assert_eq(k1, k2)
def c04():
    deep = {"a": [{"b": [{"c": [{"d": "leaf"}]}]}]}
    k1 = cachekey.compute_key(deep)
    k2 = cachekey.compute_key({"a": [{"b": [{"c": [{"d": "leaf"}]}]}]})
    assert_eq(k1, k2)
def c05():
    big = {"p": "x" * 100000}
    k1 = cachekey.compute_key(big)
    k2 = cachekey.compute_key({"p": "x" * 99999 + "x"})
    assert_eq(k1, k2)
def c06():
    k1 = cachekey.compute_key({"p": "x" * 100000 + "!"})
    k2 = cachekey.compute_key({"p": "x" * 100000})
    assert_true(k1 != k2)
def c07():
    k1 = cachekey.compute_key({"p": "line1\nline2\ttab"})
    k2 = cachekey.compute_key({"p": "line1 line2 tab"})
    assert_eq(k1, k2)
def c08():
    v = ("vol",)
    k1 = cachekey.compute_key({"p": "x", "nested": {"vol": 1, "keep": 2}}, volatile=v)
    k2 = cachekey.compute_key({"p": "x", "nested": {"keep": 2}}, volatile=v)
    assert_eq(k1, k2)
def c09():
    k1 = cachekey.compute_key({"p": "x"}, params={"b": 2, "a": 1})
    k2 = cachekey.compute_key({"p": "x"}, params={"a": 1, "b": 2})
    assert_eq(k1, k2)
def c10():
    k1 = cachekey.compute_key({"p": "x"}, params=None)
    k2 = cachekey.compute_key({"p": "x"}, params={})
    assert_eq(k1, k2)
def c11():
    k1 = cachekey.compute_key({"p": "\u30a2\u30a4\u30a6"}, namespace="\u65e5\u672c\u8a9e")
    k2 = cachekey.compute_key({"p": "\u30a2\u30a4\u30a6"}, namespace="\u65e5\u672c\u8a9e")
    assert_eq(k1, k2)
    assert_true(k1.startswith("llmk1:"))
def c12():
    keys = set(cachekey.compute_key({"p": str(i)}) for i in range(1000))
    assert_eq(len(keys), 1000)
def c13():
    assert_true(cachekey.birthday_estimate(2) >= 0.0)
def c14():
    k1 = cachekey.compute_key({"p": "x", "arr": [1, 2]})
    k2 = cachekey.compute_key({"p": "x", "arr": [2, 1]})
    assert_true(k1 != k2, "list order matters (documented)")
def c15():
    k1 = cachekey.compute_key({"p": "  A  "})
    k2 = cachekey.compute_key({"p": "a"})
    assert_true(k1 != k2, "no case folding by default (documented)")
def c16():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    try:
        ks = [cachekey.compute_key({"p": i}) for i in range(5)]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(ks + ks[:2]) + "\n")
        code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cachekey.py"), "collide", path], capture_output=True, text=True)
        assert_eq(code.returncode, 0)
        rep = json.loads(code.stdout)
        assert_eq(rep["collisions"], 2)
    finally:
        os.unlink(path)

for fn in sorted([v for k, v in list(globals().items()) if k.startswith(("a0", "a1", "a2", "b0", "b1", "c0", "c1"))], key=lambda f: f.__name__):
    check(fn.__name__, fn)


# ---------- [R2] round-2 additions (number normalization, deep volatile, cross-call determinism) ----------
def r201():
    k1 = cachekey.compute_key({"p": "x", "n": 1.0})
    k2 = cachekey.compute_key({"p": "x", "n": 1})
    assert_eq(k1, k2, "integral floats normalize to ints")
def r202():
    k1 = cachekey.compute_key({"p": "x", "n": 1.25})
    k2 = cachekey.compute_key({"p": "x", "n": 1.25000})
    assert_eq(k1, k2)
def r203():
    k1 = cachekey.compute_key({"p": "x", "n": 1.25})
    k2 = cachekey.compute_key({"p": "x", "n": 1.5})
    assert_true(k1 != k2)
def r204():
    v = ("ts",)
    k1 = cachekey.compute_key({"a": [{"ts": 1, "v": "q"}, {"ts": 2, "v": "r"}]}, volatile=v)
    k2 = cachekey.compute_key({"a": [{"v": "q"}, {"v": "r"}]}, volatile=v)
    assert_eq(k1, k2, "volatile stripped inside list items")
def r205():
    k1 = cachekey.compute_key({"p": "\u0041\u030a"}, )
    k2 = cachekey.compute_key({"p": "\u00c5"})
    assert_eq(k1, k2, "NFC composes A+ring")
def r206():
    ks = [cachekey.compute_key({"p": "p%d" % i}, namespace="n%d" % (i % 3)) for i in range(300)]
    r = cachekey.collision_test(ks)
    assert_eq(r["collisions"], 0)
def r207():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cachekey.py"), "key", "--help"], capture_output=True, text=True)
    assert_true("--volatile" in code.stdout)
def r208():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        open(path, "w", encoding="utf-8").write('{"prompt": "  a  b  ", "temperature": 0.9}')
        code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cachekey.py"), "key", path, "--volatile", "temperature", "--json"], capture_output=True, text=True)
        assert_eq(code.returncode, 0)
        out = json.loads(code.stdout)
        assert_true(out["key"].startswith("llmk1:default:"))
    finally:
        os.unlink(path)
def r209():
    import copy
    deep = {"a": {"b": {"c": {"d": "deep leaf"}}}}
    snap = copy.deepcopy(deep)
    cachekey.compute_key(deep, volatile=("zzz",))
    assert_eq(deep, snap, "compute_key must not mutate payload")
def r210():
    try:
        cachekey.compute_key(None)
        assert False
    except TypeError:
        pass
def r211():
    assert_true(cachekey.birthday_estimate(10 ** 12) > 0)
def r212():
    k1 = cachekey.compute_key({"p": "x"}, params={"a": [1, {"b": 2.0}]})
    k2 = cachekey.compute_key({"p": "x"}, params={"a": [1, {"b": 2}]})
    assert_eq(k1, k2)

for fn in sorted([v for k, v in list(globals().items()) if k.startswith("r2")], key=lambda f: f.__name__):
    check(fn.__name__, fn)

passed = sum(1 for _, ok_ in RESULTS if ok_)
for n, ok_ in RESULTS:
    if not ok_:
        print("FAIL:", n)
print("SUMMARY: PASS %d/%d" % (passed, len(RESULTS)))
sys.exit(0 if passed == len(RESULTS) else 1)
