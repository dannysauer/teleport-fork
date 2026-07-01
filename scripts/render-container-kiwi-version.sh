#!/usr/bin/env bash
# Copyright 2025 Danny Sauer and contributors
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

version="${1:?usage: render-container-kiwi-version.sh VERSION KIWI_FILE}"
kiwi_file="${2:?usage: render-container-kiwi-version.sh VERSION KIWI_FILE}"

if ! printf '%s' "$version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([-.+][0-9A-Za-z.-]+)?$'; then
  echo "invalid release version: $version" >&2
  exit 1
fi

python3 - "$version" "$kiwi_file" <<'PY'
import pathlib
import re
import sys

version = sys.argv[1]
kiwi_path = pathlib.Path(sys.argv[2])
text = kiwi_path.read_text(encoding="utf-8")

patterns = [
    (
        r'(<label name="org\.opencontainers\.image\.version" value=")[^"]+("/>)',
        rf"\g<1>{version}\2",
    ),
    (
        r"(<history author=\"Teleport Autobuild &lt;noreply@github\.com&gt;\">Teleport )[^<]+( container</history>)",
        rf"\g<1>{version}\2",
    ),
    (
        r"(<version>)[^<]+(</version>)",
        rf"\g<1>{version}\2",
    ),
]

for pattern, replacement in patterns:
    text, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"failed to update {pattern!r} in {kiwi_path}")

kiwi_path.write_text(text, encoding="utf-8")
PY
