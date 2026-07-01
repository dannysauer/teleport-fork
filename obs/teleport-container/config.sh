#!/bin/bash
# Copyright 2025 Danny Sauer and contributors
# SPDX-License-Identifier: Apache-2.0
#
# KIWI post-install script - runs inside the image during the build.
# Use this for one-time setup that can't be done via package install.

test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

# Ensure runtime directories exist with correct permissions.
# The teleport RPM should already create these, but be explicit.
mkdir -p /var/lib/teleport
chmod 700 /var/lib/teleport

mkdir -p /etc/teleport
chmod 755 /etc/teleport

# Clean up package manager caches to reduce image size.
zypper clean --all 2>/dev/null || true
rm -rf /var/cache/zypp /var/log/zypp

# Remove shell history if any.
rm -f /root/.bash_history
