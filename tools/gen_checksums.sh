#!/usr/bin/env bash
# Regenerate schema/CHECKSUMS.sha256 over the mirrored certificate-format files.
# Content is LF-normalized before hashing so the public and private repos agree
# regardless of each checkout's CRLF handling.
set -euo pipefail
cd "$(dirname "$0")/.."
FILES="schema/certificate.v1.schema.json tools/cert_hash.py docs/characterization.md contracts/q2-anchor/src/lib.rs contracts/q2-verifier/src/lib.rs contracts/q2-composition/src/lib.rs contracts/q2-anchor/abi/IQ2Anchor.sol"
{
  sed -n '1,6p' schema/CHECKSUMS.sha256
  for f in $FILES; do [ -f "$f" ] && printf '%s  %s\n' "$(tr -d '\r' < "$f" | sha256sum | cut -d' ' -f1)" "$f"; done
} > schema/CHECKSUMS.sha256.tmp
mv schema/CHECKSUMS.sha256.tmp schema/CHECKSUMS.sha256
echo "wrote schema/CHECKSUMS.sha256"
