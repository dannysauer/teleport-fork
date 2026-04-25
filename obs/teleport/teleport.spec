# Copyright 2025 Danny Sauer and contributors
# SPDX-License-Identifier: Apache-2.0
#
# This spec file is licensed under Apache-2.0.
# The Teleport software it packages is licensed under AGPL-3.0-only.

%global debug_package %{nil}

# Translate RPM arch names to Go arch names
%ifarch x86_64
%global go_arch    amd64
%global rust_triple x86_64-unknown-linux-gnu
%endif
%ifarch aarch64
%global go_arch    arm64
%global rust_triple aarch64-unknown-linux-gnu
%endif

Name:           teleport
# Version is updated automatically by obs set_version service / prep-obs-source.yml
Version:        19.0.0
Release:        1%{?dist}
Summary:        Identity-aware access proxy for infrastructure
License:        AGPL-3.0-only
URL:            https://github.com/gravitational/teleport
Source0:        teleport-%{version}.tar.gz
# Pre-built webassets (built with Node/pnpm in GitHub Actions)
Source1:        teleport-%{version}-webassets.tar.gz
# Pre-vendored Rust deps for fdpass-teleport (from GitHub Actions cargo vendor)
Source2:        teleport-%{version}-fdpass-vendor.tar.gz
Patch0:         0001-implement-oidc-service-for-oss-sso-login.patch

BuildRequires:  go >= 1.25
BuildRequires:  rust >= 1.94
BuildRequires:  cargo
BuildRequires:  clang
BuildRequires:  llvm
BuildRequires:  libbpf-devel
BuildRequires:  pam-devel
BuildRequires:  libfido2-devel
BuildRequires:  pkgconfig
BuildRequires:  git-core
BuildRequires:  make
BuildRequires:  gcc
BuildRequires:  glibc-devel
BuildRequires:  shasum

Requires:       glibc
Requires:       libpam0
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
Teleport is an identity-aware, multi-protocol access proxy for your
infrastructure. It provides certificate-based authentication and
authorization for SSH, Kubernetes, databases, Windows desktops, and
web applications — with session recording, audit logging, and RBAC.

%prep
%setup -q -n teleport-%{version}

# Extract pre-built webassets alongside the source tree.
# The webassets/ directory includes the oss-sha file; this causes the
# build-webassets-if-changed.sh script (called by 'make full') to detect
# that the assets are already up to date and skip rebuilding, without
# needing Node or pnpm in the build environment.
tar xzf %{SOURCE1}

# Extract pre-vendored Rust dependencies for fdpass-teleport.
tar xzf %{SOURCE2}

# Apply patches from the autobuild branch patches/ directory.
%patch -P0 -p1

%build
export GOFLAGS="-mod=vendor"
export GOPROXY="off"
export GONOSUMCHECK="*"
export GONOSUMDB="*"
export GOPATH="%{_builddir}/gopath"

# BPF support requires these headers to be present.
# common.mk checks for /usr/include/linux/bpf.h and /usr/include/bpf/bpf_helpers.h.
# libbpf-devel provides both on Tumbleweed.

make \
    OS=linux \
    ARCH=%{go_arch} \
    BUILDDIR="%{_builddir}/teleport-bin" \
    WEBASSETS_SKIP_BUILD=0 \
    RDPCLIENT_SKIP_BUILD=1 \
    PIV=no \
    full

%install
install -Dm755 %{_builddir}/teleport-bin/teleport        %{buildroot}%{_bindir}/teleport
install -Dm755 %{_builddir}/teleport-bin/tctl            %{buildroot}%{_bindir}/tctl
install -Dm755 %{_builddir}/teleport-bin/tsh             %{buildroot}%{_bindir}/tsh
install -Dm755 %{_builddir}/teleport-bin/tbot            %{buildroot}%{_bindir}/tbot
install -Dm755 %{_builddir}/teleport-bin/fdpass-teleport %{buildroot}%{_bindir}/fdpass-teleport
install -Dm755 %{_builddir}/teleport-bin/teleport-update %{buildroot}%{_bindir}/teleport-update

# Systemd service unit
install -Dm644 examples/systemd/teleport.service \
    %{buildroot}%{_unitdir}/teleport.service

# Configuration directory
install -dm700 %{buildroot}%{_sysconfdir}/teleport
install -dm700 %{buildroot}%{_localstatedir}/lib/teleport

%post
%systemd_post teleport.service

%preun
%systemd_preun teleport.service

%postun
%systemd_postun_with_restart teleport.service

%files
%license LICENSE
%doc README.md
%{_bindir}/teleport
%{_bindir}/tctl
%{_bindir}/tsh
%{_bindir}/tbot
%{_bindir}/fdpass-teleport
%{_bindir}/teleport-update
%{_unitdir}/teleport.service
%dir %attr(700,root,root) %{_sysconfdir}/teleport
%dir %attr(700,root,root) %{_localstatedir}/lib/teleport

%changelog
* Thu Apr 01 2026 Teleport Autobuild <noreply@github.com> - 19.0.0-1
- Automated build from upstream
