# Setting Up Your Own Build Pipeline

This document walks through reproducing the full build pipeline in your own fork.
It assumes you already have a GitHub account and an account on
[build.opensuse.org](https://build.opensuse.org) (OBS).

---

## 1. Fork this automation repository

Fork `dannysauer/teleport-fork` on GitHub.  You will end up with
`github.com/YOU/teleport-fork` (or whatever name you choose). The `master`
branch is kept as a clean mirror of `gravitational/teleport`; the build
automation lives on the `autobuild` branch.

In your fork's **Settings → General → Default branch**, switch the default
branch from `master` to `autobuild`.

---

## 2. Add GitHub Actions credentials

The workflows need an OBS trigger token and a GitHub App token source.

Add these repository secrets:

| Secret | Purpose |
|--------|---------|
| `OBS_TRIGGER_TOKEN` | OBS service-run trigger token created in step 6 |
| `APP_PRIVATE_KEY` | Private key for a GitHub App installed on this repository |

Add this repository variable:

| Variable | Purpose |
|----------|---------|
| `APP_ID` | App ID for the same GitHub App |

The GitHub App must have **Contents: write**, **Workflows: write**, and
**Actions: write** on this repository. The App token is needed because `master`,
`obs-build-source`, and upstream tags contain Teleport's upstream workflow
files; `GITHUB_TOKEN` cannot push workflow-file changes. The same token also
dispatches `prep-obs-source.yml` after a new tag is mirrored.

---

## 3. Create the OBS project

Log in to [build.opensuse.org](https://build.opensuse.org) and use your home
project, e.g. `home:YOU`. This repository's checked-in configuration uses
`home:dannysauer`.

### 3a. Set the project config (`prjconf`)

In the OBS web UI, go to your project → **Project Config** tab, and add:

```
PublishFlags: withcontainers
```

This is only needed if you later wire the optional KIWI container package.

### 3b. Configure build repositories

Under **Repositories**, add:

| Name | Build against |
|------|---------------|
| `openSUSE_Tumbleweed` | `openSUSE:Factory` standard Tumbleweed repo |
| `Ubuntu_24.04` | `Ubuntu:24.04` standard Ubuntu repo |

---

## 4. Create the `gravitational_teleport` package in OBS

In your OBS project, create a new package named **`gravitational_teleport`** and upload
**only `obs/teleport/_service`**.  That is the only file OBS needs from you.

After `prep-obs-source.yml` has published the build assets, OBS service runs will:
- Fetch the Teleport source tarball from the `obs-build-source` branch, which
  points at the newest upstream stable `vX.Y.Z` tag selected from all upstream
  tags, including release branches
- Fetch `teleport.spec` and `debian.*` packaging files from the
  `obs-build-inputs` branch
- Fetch vendored Go modules, pre-built web assets, fdpass binaries, and Go toolchains from the
  `obs-build-assets` branch

You can upload `_service` via the OBS web UI or the `osc` CLI:

```bash
osc checkout home:YOU
cp obs/teleport/_service home:YOU/gravitational_teleport/
cd home:YOU/gravitational_teleport
osc add _service
osc commit -m "bootstrap gravitational_teleport package"
```

> **Note:** The `_service` file references `github.com/dannysauer/teleport-fork`.
> If you are reproducing this under your own account, update the
> `<param name="url">` values before uploading.

---

### Bootstrap ordering

The `_service` file fetches assets from the GitHub `obs-build-assets` branch.
That branch does not exist until `prep-obs-source.yml` runs for the first target
tag. A first OBS service run can fail during bootstrap; run `prep-obs-source.yml`
manually for the tag you want to build, verify the `obs-build-assets` branch
exists, then re-run services or push to `autobuild` to trigger OBS.

---

## 5. Optional container package

`obs/teleport-container/` is a scaffold, not part of the active RPM/Deb trigger
path. Do not document or publish `ghcr.io` images or Helm charts from it until
the container package is wired to the same `obs-build-source` version flow.

Create a new OBS package named **`teleport-container`** before running these
commands:

```bash
osc checkout home:YOU
cp obs/teleport-container/_service home:YOU/teleport-container/
cd home:YOU/teleport-container
osc add _service
osc commit -m "bootstrap teleport-container package"
```

---

## 6. Create an OBS trigger token

OBS trigger tokens let GitHub Actions fire a service re-run on a specific
package without storing your OBS credentials anywhere.

In the OBS web UI, navigate to your project's **gravitational_teleport** package:

Profile → **Trigger tokens** → New token

- Token type: **Trigger service run**
- Linked package: `home:YOU / gravitational_teleport`

Copy the token value and store it as the `OBS_TRIGGER_TOKEN` GitHub secret
(step 2 above).

The current workflow triggers only this package.

---

## 7. Update workflow and OBS files with your identifiers

Several files embed `dannysauer` or the full repo path.  Do a search-and-replace
before your first commit:

| File | What to change |
|------|---------------|
| `.github/workflows/sync-registry.yml` | `OBS_IMAGE` env var (OBS project path) |
| `.github/workflows/sync-registry.yml` | `GHCR_IMAGE` env var (if your image name differs) |
| `obs/teleport/_service` | `<param name="url">` — point to your fork |
| `obs/teleport-container/config.xml` | OCI label `org.opencontainers.image.source` |
| `prep-obs-source.yml` | `OBS_PROJECT` variable inside the trigger step |
| `.obs/workflows.yml` | OBS project and package names |

---

## 8. Set up OBS push-triggered service runs

The checked-in `.obs/workflows.yml` tells OBS to re-run services for the
`gravitational_teleport` package when you push the `autobuild` branch. Upload
that workflow through the OBS web UI if you want push-triggered service runs.
The GitHub workflow still uses the trigger token after it has uploaded matching
assets, which is the safer path for release builds.

`sync-registry.yml` is manual-only until the optional container package is wired.
If you later enable container publishing, configure OBS to call the
`workflow_dispatch` endpoint when a container build completes:

1. In OBS, go to your project → **Webhooks** (or package-level notifications).
2. Add a webhook pointing to:
   ```
   https://api.github.com/repos/YOU/teleport-fork/actions/workflows/sync-registry.yml/dispatches
   ```
3. OBS needs a GitHub fine-grained PAT with **Actions: write** permission on
   your repository (read access to the repo is not required).  Store it in OBS
   as the webhook secret/header value.

Treat that token as a publishing trigger because the workflow can push packages
to `ghcr.io`.

---

## 9. Trigger the first build

Use **Actions → Run workflow** on `sync-upstream.yml` to pull upstream, find the
newest stable upstream tag, and dispatch `prep-obs-source.yml` from `autobuild`
if that release has not already been prepared. Stable Teleport releases are
tagged on upstream release branches, so the workflow scans all upstream tags for
clean `vX.Y.Z` releases instead of using tags merged into `master`.

If you need to rebuild a tag that `obs-build-source` already points at, run
`prep-obs-source.yml` manually for the tag you want to build.

Pushing `autobuild` by itself only re-runs OBS services if you installed
`.obs/workflows.yml`; it does not build or upload GitHub build assets.

The release pipeline is:

1. `sync-upstream.yml` — syncs `master`, finds the latest upstream stable tag,
   pushes it to this fork if missing, and dispatches `prep-obs-source.yml` unless
   `obs-build-source` already points at that upstream tag.
2. `prep-obs-source.yml` — builds web assets and `fdpass-teleport`, updates
   `obs-build-source` to the same tag, updates `obs-build-inputs` to the
   current `autobuild` commit, updates `obs-build-assets` with matching assets
   and checksums, and calls the OBS trigger token.
3. OBS — fetches source and vendored build assets via `_service`, then builds RPM and Deb.

---

## What you still need if you are `dannysauer`

If you are working in `dannysauer/teleport-fork`, the workflows and `_service`
files already reference the correct repository and OBS project. You still need
the OBS package, OBS trigger token, and GitHub App credentials described above.

To summarise the minimum remaining work:

1. In `home:dannysauer`, create package **`gravitational_teleport`** and upload
   `obs/teleport/_service`.
2. Create an OBS trigger token (step 6) and add it as `OBS_TRIGGER_TOKEN` in
   GitHub Secrets.
3. Create or install the GitHub App from step 2, set `APP_ID`, and add
   `APP_PRIVATE_KEY`.

Then run the `sync-upstream.yml` workflow manually to kick off the first full
build.
