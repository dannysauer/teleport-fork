# OBS packaging

This directory contains the source files used by the OBS packages for the
`autobuild` branch.

## Active package flow

- `home:dannysauer/gravitational_teleport` builds the Teleport RPM and Debian
  packages from GitHub-generated OBS source branches.
- `home:dannysauer:teleport/teleport-container` builds the container image from
  the published `teleport` RPMs and mirrors it to GHCR through
  `sync-registry.yml`.

The active repository targets are:

- `xUbuntu_26.04` `x86_64` and `aarch64` for Debian packages.
- `openSUSE_Slowroll` `x86_64` for the RPM used by the x86_64 container.
- `openSUSE_Factory_ARM` `aarch64` for the RPM used by the aarch64 container.
- `home:dannysauer:teleport/container` `x86_64` and `aarch64` for the KIWI
  container image.

## Legacy OBS rows

The `home:dannysauer` project still has several inherited or historical
repositories such as old Ubuntu, Leap, SLE, RHEL, CentOS, Raspbian, Tumbleweed
i586/x86_64, and unsupported Slowroll ARM rows. They currently show as broken or
disabled in OBS and are not part of the automated release path.

Do not treat those rows as release blockers unless they are intentionally
re-enabled and wired into the GitHub workflows.
