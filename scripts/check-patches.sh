#!/usr/bin/env bash
# Copyright 2025 Danny Sauer and contributors
# SPDX-License-Identifier: Apache-2.0
#
# Verify that patches/ apply cleanly to upstream master and that any new
# Go files pass gofmt.  Used as a pre-commit hook and in CI.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
PATCHES_DIR="${REPO_ROOT}/patches"

if ! ls "${PATCHES_DIR}"/*.patch &>/dev/null; then
    echo "No patches found — nothing to check."
    exit 0
fi

# Require a local master branch or remote ref to apply against.
if ! git rev-parse --verify origin/master &>/dev/null; then
    echo "origin/master not available — skipping patch check."
    echo "(Run 'git fetch origin master' to enable.)"
    exit 0
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "${WORKDIR}"' EXIT

echo "==> Creating temporary worktree…"
git worktree add --quiet --detach "${WORKDIR}" origin/master

echo "==> Applying patches…"
for patch in "${PATCHES_DIR}"/*.patch; do
    name="$(basename "${patch}")"
    if ! git -C "${WORKDIR}" apply --check "${patch}" 2>/dev/null; then
        echo "FAIL: ${name} does not apply cleanly."
        git worktree remove --force "${WORKDIR}" 2>/dev/null || true
        exit 1
    fi
    git -C "${WORKDIR}" apply "${patch}"
    echo "  ✓ ${name}"
done

echo "==> Checking gofmt on patched Go files…"
BAD_FMT=""
for patch in "${PATCHES_DIR}"/*.patch; do
    # Extract names of new/modified .go files from the patch.
    go_files=$(grep -E '^\+\+\+ b/' "${patch}" | sed 's|^+++ b/||' | grep '\.go$' || true)
    for f in ${go_files}; do
        filepath="${WORKDIR}/${f}"
        if [ -f "${filepath}" ]; then
            if ! diff -q <(gofmt "${filepath}") "${filepath}" &>/dev/null; then
                echo "FAIL: ${f} is not gofmt-formatted."
                BAD_FMT="yes"
            fi
        fi
    done
done

git worktree remove --force "${WORKDIR}" 2>/dev/null || true

if [ -n "${BAD_FMT}" ]; then
    exit 1
fi

echo "All patches OK."
