#!/usr/bin/env python3
"""
cert_hash.py: the single place that computes a certificate's artifact_hash.

A certificate's on-chain artifact_hash is sha256 of the canonical bundle with
its `certificate` block removed. Canonical = JSON with sorted keys and no
whitespace, UTF-8. Every registration path (the contracts' demo/register and the
catalog export) must hash through this function so one bundle has exactly one
hash, and anyone holding the bundle recomputes it and checks it against the chain.

Usage:
  python tools/cert_hash.py <bundle.json>            # print the artifact_hash
  python tools/cert_hash.py <bundle.json> --write     # write it into certificate.artifact_hash
  python tools/cert_hash.py <bundle.json> --verify    # check the stored hash matches
"""
import hashlib
import json
import sys


def artifact_hash(bundle: dict) -> str:
    """sha256 of the canonical bundle, excluding the `certificate` block."""
    body = {k: v for k, v in bundle.items() if k != "certificate"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "0x" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "--print"
    bundle = json.load(open(path, encoding="utf-8"))
    h = artifact_hash(bundle)
    if mode == "--verify":
        stored = (bundle.get("certificate") or {}).get("artifact_hash")
        ok = stored == h
        print(f"{'OK' if ok else 'MISMATCH'}: computed {h}" + ("" if ok else f", stored {stored}"))
        return 0 if ok else 1
    if mode == "--write":
        bundle.setdefault("certificate", {})["artifact_hash"] = h
        json.dump(bundle, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        open(path, "a", encoding="utf-8").write("\n")
    print(h)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
