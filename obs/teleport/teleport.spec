# Copyright 2025 Danny Sauer and contributors
# SPDX-License-Identifier: Apache-2.0
#
# This spec file is licensed under Apache-2.0.
# The Teleport software it packages is licensed under AGPL-3.0-only.

%global debug_package %{nil}
%{!?_unitdir:%global _unitdir %{_prefix}/lib/systemd/system}

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
Source1:        teleport-webassets.tar.gz
# Pre-vendored Rust deps for fdpass-teleport (from GitHub Actions cargo vendor)
Source2:        teleport-fdpass-vendor.tar.gz
# Manifest and checksums for stable build assets downloaded by _service
Source3:        teleport-build-assets.env
Source4:        teleport-build-assets.sha256
# Vendored Go module dependencies from prep-obs-source.yml
Source5:        vendor.tar.gz

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
BuildRequires:  coreutils
BuildRequires:  systemd-rpm-macros

Requires:       glibc
Requires:       pam
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

# Verify that stable build-assets release files match this source version.
(cd %{_sourcedir} && sha256sum -c %{SOURCE4})
TELEPORT_VERSION=$(awk -F= '$1 == "TELEPORT_VERSION" && $2 ~ /^[0-9A-Za-z.+-]+$/ { print $2; found=1 } END { if (!found) exit 1 }' %{SOURCE3})
if [ "$TELEPORT_VERSION" != "%{version}" ]; then
    echo "build-assets version $TELEPORT_VERSION does not match source version %{version}" >&2
    exit 1
fi

# Extract pre-built webassets alongside the source tree.
# The webassets/ directory includes the oss-sha file; this causes the
# build-webassets-if-changed.sh script (called by 'make full') to detect
# that the assets are already up to date and skip rebuilding, without
# needing Node or pnpm in the build environment.
tar xzf %{SOURCE1}

# Extract pre-vendored Rust dependencies for fdpass-teleport.
tar xzf %{SOURCE2}

# Extract vendored Go module dependencies from prep-obs-source.yml.
tar xzf %{SOURCE5}

# Apply patches from the obs-build-inputs branch patches/ directory.
for patch in %{_sourcedir}/*.patch; do
    [ -e "$patch" ] || continue
    echo "Applying $patch"
    patch -p1 < "$patch"
done

%build
export GOFLAGS="-mod=vendor"
export GOPROXY="off"
export GONOSUMCHECK="*"
export GONOSUMDB="*"
export GOPATH="%{_builddir}/gopath"

# BPF support requires these headers to be present.
# common.mk checks for /usr/include/linux/bpf.h and /usr/include/bpf/bpf_helpers.h.
# libbpf-devel provides both on Tumbleweed.

# The upstream Makefile injects teleportBuildType=community via TELEPORT_LDFLAGS,
# which triggers a "you must agree to our terms" checkbox on first login that
# restricts use to companies under $10MM ARR / 100 employees.  That restriction
# applies only to Gravitational's own Community Edition binaries and cannot be
# enforced on third-party AGPL builds.  Override back to the default "oss" type.
export TELEPORT_LDFLAGS="-ldflags '-w -s'"
export TOOLS_LDFLAGS="-ldflags '-w -s'"

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
* Sat Jun 27 2026 Teleport Autobuild <noreply@github.com> - 19.0.0-1
- Automated build from upstream
